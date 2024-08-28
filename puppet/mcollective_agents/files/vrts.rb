module MCollective
  module Agent
    class Vrts<RPC::Agent
      begin
        PluginManager.loadclass("MCollective::Util::LogAction")
        log_action = Util::LogAction
      rescue LoadError => e
        raise "Cannot load logaction util: %s" % [e.to_s]
      end

      action "pull_packages" do
        log_action = Util::LogAction

        cmd = "mkdir -p #{request[:destination_dir]}"
        log_action.debug("Running command: #{cmd}", request)
        reply[:status] = run("#{cmd}",
                             :stdout => :out,
                             :stderr => :err,
                             :chomp => true)
        log_action.debug("Outcome: #{reply[:status]}", request)

        package_list = request[:packages]
        packages = package_list.split(";")
        packages.each do |package|
          source_uri = request[:source_dir_uri] + package
          dest_abs_path = File.join(request[:destination_dir], package)
          cmd = "wget #{source_uri} -O #{dest_abs_path}"
          log_action.debug("Running command: #{cmd}", request)
          reply[:status] = run("#{cmd}",
                                :stdout => :out,
                                :stderr => :err,
                                :chomp => true)
          log_action.debug("Outcome: #{reply[:status]}", request)
        end
      end

      action "clean_packages_dir" do
        log_action = Util::LogAction
        cmd = "rm -rf #{request[:destination_dir]}"
        reply[:status] = run("#{cmd}",
                              :stdout => :out,
                              :stderr => :err,
                              :chomp => true)
        log_action.debug("Outcome: #{reply[:status]}", request)
      end

      action "rpm_remove_packages" do
        log_action = Util::LogAction
        cmd = "rpm -e #{request[:packages]}"
        log_action.debug("Running command: #{cmd}", request)
        reply[:status] = run("#{cmd}",
                              :stdout => :out,
                              :stderr => :err,
                              :chomp => true)
        log_action.debug("Outcome: #{reply[:status]}", request)
      end

      action "rpm_upgrade_packages" do
        log_action = Util::LogAction
        package_list = request[:packages]
        packages = package_list.split(";")
        rpm_dir = request[:destination_dir]
        packages.each do |package|
          abs_path = File.join(rpm_dir, package)
          cmd ="rpm -Uvh #{abs_path}"
          log_action.debug("Running command: #{cmd}", request)
          reply[:status] = run("#{cmd}",
                                :stdout => :out,
                                :stderr => :err,
                                :chomp => true)
          log_action.debug("Outcome: #{reply[:status]}", request)
        end
      end

      action "update_licence" do
        log_action = Util::LogAction
        cmd = "/opt/VRTS/bin/vxkeyless set -q ENTERPRISE"
        reply[:status] = run("#{cmd}",
                              :stdout => :out,
                              :stderr => :err,
                              :chomp => true)
        log_action.debug("Outcome: #{reply[:status]}", request)
      end

      action "remove_vrtsfsadv" do
        log_action = Util::LogAction
        cmd = "/usr/bin/systemctl reset-failed vxfs_replication.service"
        reply[:retcode] = run("#{cmd}",
                             :stdout => :out,
                             :stderr => :err,
                             :chomp => true)
        log_action.debug("Outcome: reset-failed vxfs_replication service #{reply[:status]}", request)
        cmd = "yum erase -y VRTSfsadv"
        reply[:retcode] = run("#{cmd}",
                             :stdout => :out,
                             :stderr => :err,
                             :chomp => true)
        log_action.debug("Outcome: yum remove VRTSfsadv #{reply[:status]}", request)
      end

      action "disable_vxvm_boot" do
        log_action = Util::LogAction
        cmd = "/usr/bin/systemctl disable vxvm-boot.service"
        reply[:status] = run("#{cmd}",
                              :stdout => :out,
                              :stderr => :err,
                              :chomp => true)
        log_action.debug("Outcome: #{reply[:status]}", request)
      end
    end
  end
end
