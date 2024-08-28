module MCollective
  module Agent
    class Yum<RPC::Agent
      begin
        PluginManager.loadclass("MCollective::Util::LogAction")
        log_action = Util::LogAction
      rescue LoadError => e
        raise "Cannot load logaction util: %s" % [e.to_s]
      end

      action "get_packages" do
        cmd = "repoquery -q --qf \'%{name} %{version} %{release} %{arch}\' -a --pkgnarrow=updates --repoid=UPDATES --repoid=OS --repoid=LITP --repoid=3PP --plugins"
        reply[:status] = run("#{cmd}",
                              :stdout => :out,
                              :stderr => :err,
                              :chomp => true)

      end
      action "get_all_packages" do
        cmd = "repoquery -q --qf \'%{name} %{version} %{release} %{arch}\' -a --pkgnarrow=updates --plugins"
        reply[:status] = run("#{cmd}",
                              :stdout => :out,
                              :stderr => :err,
                              :chomp => true)

      end
      action "upgrade_package" do
        cmd = "yum update -y #{request[:name]} --setopt=protected_multilib=false"
        reply[:status] = run("#{cmd}",
                              :stdout => :out,
                              :stderr => :err,
                              :chomp => true)
      end
      action "upgrade_all_packages" do
        log_action = Util::LogAction

        cmd = "yum update -y --setopt=protected_multilib=false || (yum clean metadata && yum update -y --setopt=protected_multilib=false)"
        log_action.log("upgrade_all_packages", "Running command: #{cmd}")
        reply[:status] = run("#{cmd}",
                              :stdout => :out,
                              :stderr => :err,
                              :chomp => true)
      end
      action "complete_transaction" do
        cmd = "yum-complete-transaction -y"
        reply[:status] = run("#{cmd}",
                              :stdout => :out,
                              :stderr => :err,
                              :chomp => true)
      end

      action "set_state_vcs_services" do
        log_action = Util::LogAction

        commands_str = request[:commands_str]
        commands = commands_str.split(";")

        commands.each do |cmd|
          if cmd.include?('haconf') or cmd.include?('vxfen start') then
             allowed_rcs = [0,1]
          else
             allowed_rcs = [0]
          end

          if cmd.include?('llt stop') then
             tries = 5
          else
             tries = 1
          end

          if cmd.include?('hastart') then
            sleep_duration = 10
          else
            sleep_duration = 5
          end

          tries.times do
             log_action.debug("Running command: #{cmd}", request)
             reply[:status] = run("#{cmd}",
                                  :stdout => :out,
                                  :stderr => :err,
                                  :chomp => true)
             log_action.debug("Outcome: #{reply[:status]}", request)
             break if allowed_rcs.include?(reply[:status])
             sleep sleep_duration
          end

          if allowed_rcs.include?(reply[:status]) then
            reply[:status] = 0
            reply[:err] = ""
          else
             break
          end
          log_action.debug("Will sleep for #{sleep_duration}", request)
          sleep sleep_duration
        end
      end

      action "vcs_status" do
        log_action = Util::LogAction
        reply[:status] = run("/opt/VRTSvcs/bin/hastatus -sum",
                             :stdout => :out,
                             :stderr => :err,
                             :chomp => true)
        log_action.debug("Outcome: #{reply[:status]}", request)
      end

      action "replace_package" do
        log_action = Util::LogAction
        cmd = "rpm -q #{request[:replacement]} && yum list #{request[:replacement]}"
        pre_req_hash = {:out => "", :err => ""}
        pre_req_hash[:status] = run("#{cmd}",
                                     :stdout => pre_req_hash[:out],
                                     :stderr => pre_req_hash[:err],
                                     :chomp => true)

        if pre_req_hash[:status] == 0
          cmd = "rpm -e --nodeps -- #{request[:replacement]} 2>/dev/null"
          reply[:status] = run("#{cmd}",
                                :stdout => :out,
                                :stderr => :err,
                                :chomp => true)
          if reply[:status] != 0
            return
          end
        end

        cmd = "rpm -q #{request[:replaced]} && yum list #{request[:replaced]}"
        pre_req_hash = {:out => "", :err => ""}
        pre_req_hash[:status] = run("#{cmd}",
                                     :stdout => pre_req_hash[:out],
                                     :stderr => pre_req_hash[:err],
                                     :chomp => true)

        if pre_req_hash[:status] == 0
          cmd = "rpm -e --nodeps -- #{request[:replaced]} 2>/dev/null"
          reply[:status] = run("#{cmd}",
                                :stdout => :out,
                                :stderr => :err,
                                :chomp => true)
          if reply[:status] != 0
            return
          end
        end

        cmd = "yum install -y -- #{request[:replacement]}"
        reply[:status] = run("#{cmd}",
                              :stdout => :out,
                              :stderr => :err,
                              :chomp => true)

        if reply[:err].include?('os.rename(rpmdbvfname + ".tmp", rpmdbvfname)')
          log_action.log("replace_package", "yum rpmdb-indexes /var/lib/yum/rpmdb-indexes/version.tmp file missing, retrying install command: #{cmd}")
          sleep 2
          reply[:status] = run("#{cmd}",
                                :stdout => :out,
                                :stderr => :err,
                                :chomp => true)
        end
      end

    end
  end
end
