require 'syslog'
require 'facter'

module MCollective
  module Agent
    class Dmp<RPC::Agent
      begin
        PluginManager.loadclass("MCollective::Util::LogAction")
        log_action = Util::LogAction
      rescue LoadError => e
        raise "Cannot load logaction util: %s" % [e.to_s]
      end

      action "lvm_filter" do
        log_action = Util::LogAction
        res = `grep global_filter /etc/lvm/lvm.conf | grep -v \\#`
        log_action.debug("Before changing lvm filter: #{res}", request)
        if request[:action] == 'off'
            # /global_filter = \\[/ -> only replace lines starting with global_filter = [
            # we want to replace anything between [], because the global filter should be entirely replaced
            # only reject /dev/vx/dmp devices, which belong to Veritas DMP. Leave the rest
            # the duplicate VG messages appearing due to sd* and Linux Multipather should not be something to worry about,
            # since they will appear only when the vxvm rpm is being updated.
            log_action.debug('Replacing contents of global filter with r|/dev/vx/dmp/|, r|/dev/Vx.*|', request)
            cmd = "sed -i -e '/global_filter = \\[/s@global_filter = \\[.*\\]@global_filter = \[ \"r\|/dev/vx/dmp/\|\", \"r\|/dev/Vx.*\|\" ]@g' /etc/lvm/lvm.conf"
            reply[:status] = run("#{cmd}",
                                 :stdout => :out,
                                 :stderr => :err,
                                 :chomp => true)
        elsif request[:action] == 'on'
            # /global_filter = \\[ -> look for global_filter = [
            # /s/]$ -> go to the end of the string
            # , \"r\|\^/dev/sd\.\*\|\", ] -> and substitute it with , "r|^/dev/sd.*|", ]
            log_action.debug('Appending r|^/dev/sd.*| to global_filter', request)
            cmd = "sed -i -e '/global_filter = \\[/s@]$@, \"r\|\^/dev/sd\.\*\|\", ]@g' /etc/lvm/lvm.conf"
            reply[:status] = run("#{cmd}",
                                 :stdout => :out,
                                 :stderr => :err,
                                 :chomp => true)
        end
        res = `grep global_filter /etc/lvm/lvm.conf | grep -v \\#`
        log_action.debug("After changing lvm filter: #{res}", request)
      end

      def log_global_filter(label, prefix, support)
        log_action = Util::LogAction
        res = `/bin/grep global_filter /etc/lvm/lvm.conf | /bin/grep -v \\#`
        log_action.log(label, "#{prefix} VxDMP dmp_native_support update to \"#{support}\": #{res}")
      end

      def get_ramdisk_udev_pv_uuid(label, rd_file_name)
        log_action = Util::LogAction
        path='/usr/bin'
        if (Facter.value(:operatingsystemmajrelease).to_i < 7)
          path = '/sbin'
        end
        vxdmp_pv_uuid = `#{path}/lsinitrd #{rd_file_name} /etc/udev/rules.d/84-vxvm.rules | /bin/grep UUID | /usr/bin/head -1 | /bin/sed -e 's/^ENV{ID_FS_UUID_ENC}!="\\([^"]*\\)", GOTO="vxvm_end"$/\\1/g'`
        cleaned_vxdmp_pv_uuid = vxdmp_pv_uuid.strip
        log_action.log(label, "VxDMP initrd UDev UUID: \"#{cleaned_vxdmp_pv_uuid}\"")
        return cleaned_vxdmp_pv_uuid
      end

      def get_system_pv_ids(label, desc)
        log_action = Util::LogAction
        root_pv_ids = `for path in $(/sbin/pvs --noheadings 2> /dev/null | /bin/grep -w vg_root | /bin/awk '{print $1}'); do /sbin/blkid -s UUID -o value ${path}; done`.split()
        cleaned_root_pv_ids = root_pv_ids.map{|x| x.strip}.compact
        log_action.log(label, "#{desc}: \"#{cleaned_root_pv_ids.join(', ')}\"")
        return cleaned_root_pv_ids
      end

      def get_default_kernel_version(label)
        log_action = Util::LogAction
        default_kernel_image = `/sbin/grubby --default-kernel`
        default_kernel_version = default_kernel_image.strip.split('-', 2)[1]
        log_action.log(label, "Default kernel version \"#{default_kernel_version}\"")
        return default_kernel_version
      end

      def get_vx_ramdisk_file_name(label, default_kernel_version)
        log_action = Util::LogAction
        initrd_file = "/boot/VxDMP_initrd-#{default_kernel_version}"
        log_action.log(label, "VxDMP RAM disk file \"#{initrd_file}\"")
        return initrd_file
      end

      def regenerate_vx_ramdisk(label, default_kernel_version, initrd_file)
        log_action = Util::LogAction
        cmd = "/bin/mv -f #{initrd_file} #{initrd_file}.bad.#{Time.now.strftime("%Y.%m.%d-%H.%M.%S")}"
        res = run("#{cmd}", :stdout => :out, :stderr => :err, :chomp => true)
        log_action.log(label, "Ran command \"#{cmd}\", result: #{res}")

        cmd = "/etc/vx/bin/vxinitrd dmproot #{initrd_file} #{default_kernel_version}"
        log_action.log(label, "Running command: \"#{cmd}\" ...")
        res = run("#{cmd} 2>&1", :stdout => :out, :stderr => :err, :chomp => true)
        log_action.log(label, "vxinitrd command result: #{res}")
      end

      def compare_pv_ids(label, initrd_file)
        desc = 'System vg_root PV ID(s)'
        root_pv_ids = get_system_pv_ids(label, desc)
        vxdmp_pv_uuid = get_ramdisk_udev_pv_uuid(label, initrd_file)
        msg_tmplt = "#{desc} \"#{root_pv_ids.join(', ')}\" %s VxDMP_initrd PV ID \"#{vxdmp_pv_uuid}\""
        if root_pv_ids.include?(vxdmp_pv_uuid)
          return true, msg_tmplt % ['match']
        else
          return false, msg_tmplt % ['do NOT match']
        end
      end

      def mask_boot_mount(label, action, expected_err)
        # TORF-622466 & TORF-710159 workaround for intermittent /boot mount issues in RHEL7.
        # Systemd and the Veritas code may both attempt to umount and mount /boot at the same time.
        # Masking the boot.mount for the periods of disabling and re-enabling VxDMP Native Support will
        # prevent those issues from arising.
        # This workaround can probably be removed in RHEL9 if systemd issues have been resolved in that release.
        log_action = Util::LogAction
        log_action.log(label, "#{action}ing systemctl boot.mount")
        cmd = "/usr/bin/systemctl --runtime #{action} boot.mount"
        reply[:status] = run("#{cmd}",
                             :stdout => :out,
                             :stderr => :err,
                             :chomp => true)
        log_action.log(label, "Command \"#{cmd}\", result: \"#{reply[:status]}\". out: \"#{reply[:out]}\". err: \"#{reply[:err]}\"")
        if reply[:err].include?("#{expected_err}")
            log_action.log(label, "Resetting expected err \"#{reply[:err]}\" generated by command \"#{cmd}\"")
            reply[:err] = ""
        end
      end

      action "dmp_config" do
        label = "dmp:dmp_config"
        support = request[:action]

        log_global_filter(label, 'Before', support)

        # TORF-622466 & TORF-710159 workaround for intermittent /boot mount issues in RHEL7.
        # This workaround can probably be removed in RHEL9 if systemd issues have been resolved in that release.
        mask_boot_mount(label, "mask", "Created symlink from /run/systemd/system/boot.mount to /dev/null")

        cmd = "/sbin/vxdmpadm settune dmp_native_support=#{support}"
        reply[:status] = run("#{cmd}",
                             :stdout => :out,
                             :stderr => :err,
                             :chomp => true)

        # The exit code 215 means migration was successful and now reboot is required.
        if reply[:status] == 215
          reply[:status] = 0
        end

        # TORF-622466 & TORF-710159 workaround for intermittent /boot mount issues in RHEL7.
        # This workaround can probably be removed in RHEL9 if systemd issues have been resolved in that release.
        mask_boot_mount(label, "unmask", "Removed symlink /run/systemd/system/boot.mount")

        log_global_filter(label, 'After', support)

        if support == 'on' and reply[:status] == 0
          default_kernel_version = get_default_kernel_version(label)
          initrd_file = get_vx_ramdisk_file_name(label, default_kernel_version)

          match1, message1 = compare_pv_ids(label, initrd_file)
          if not match1
            log_action.log(label, message1)

            log_action.log(label, 'Performing LVM recovery and ramdisk regeneration ...')

            vxupdatelvm = '/usr/lib/vxvm/bin/vxupdatelvm'
            tmp_file1 = '/tmp/dmpnode'
            tmp_file2 = '/tmp/error'
            cmds = ["#{vxupdatelvm} remove_global_filter",
                    "/bin/touch #{tmp_file1} #{tmp_file2}",
                    "#{vxupdatelvm} enable #{tmp_file1} #{tmp_file2}",
                    "#{vxupdatelvm} verify",
                    '/sbin/vgchange --refresh',
                    "/bin/rm -f #{tmp_file1} #{tmp_file2}"]
            cmds.each do |cmd|
              res = run("#{cmd} 2>&1",
                        :stdout => :out, :stderr => :err, :chomp => true)
              log_action.log(label, "Command: \"#{cmd}\", result: #{res}")
            end

            regenerate_vx_ramdisk(label, default_kernel_version, initrd_file)

            match2, message2 = compare_pv_ids(label, initrd_file)
            if not match2
              log_action.log(label, message2)
              reply[:status] = 1
              reply[:out] = ""
              reply[:err] = message2
            else
              log_action.log(label, message2)
            end
          else
            log_action.log(label, message1)
          end
        end
      end

      action "check_migrate_native_exists_and_remove" do
        cmd = "/bin/ls /etc/vx/.migrate_native && /bin/rm -f /etc/vx/.migrate_native || true"
        reply[:status] = run("#{cmd}",
                             :stdout => :out,
                             :stderr => :err,
                             :chomp => true)
      end
    end
  end
end
