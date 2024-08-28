metadata :name        => "vrts",
         :description => "Agent to handle vrts operations",
         :author      => "Ericsson AB",
         :license     => "Ericsson",
         :version     => "1.0",
         :url         => "http://ericsson.com",
         :timeout     => 1800

action "pull_packages", :description => "Fetch packages to node" do
    display :always

    input :source_dir_uri,
          :prompt      => "URI for the source of packages",
          :description => "URI for the source of packages",
          :type        => :string,
          :validation  => /^.+$/,
          :optional    => false,
          :maxlength   => 100

    input :destination_dir,
          :prompt      => "destination directory",
          :description => "directory where packages will be written to",
          :type        => :string,
          :validation  => /^.+$/,
          :optional    => false,
          :maxlength   => 100

    input :packages,
          :prompt      => "Names of RPMs to be pulled",
          :description => "Names of RPMs to be pulled",
          :type        => :string,
          :validation  => /^.+$/,
          :optional    => false,
          :maxlength   => 0

    output :status,
           :description => "The output of the command",
           :display_as  => "Command result",
           :default     => "no output"
end

action "clean_packages_dir", :description => "Delete packages from node" do
    display :always

    input :destination_dir,
          :prompt      => "destination directory",
          :description => "directory from which packages will be removed",
          :type        => :string,
          :validation  => /^.+$/,
          :optional    => false,
          :maxlength   => 100

    output :status,
           :description => "The output of the command",
           :display_as  => "Command result",
           :default     => "no output"
end

action "rpm_remove_packages", :description => "Remove packages from node using RPM commands" do
    display :always

    input :packages,
          :prompt      => "Names of RPMs to be removed",
          :description => "Names of RPMs to be removed",
          :type        => :string,
          :validation  => /^.+$/,
          :optional    => false,
          :maxlength   => 800

    output :status,
           :description => "The output of the command",
           :display_as  => "Command result",
           :default     => "no output"
end

action "rpm_upgrade_packages", :description => "Upgrade packages on node using RPM commands" do
    display :always

    input :destination_dir,
          :prompt      => "destination directory",
          :description => "directory with packages to be upgraded",
          :type        => :string,
          :validation  => /^.+$/,
          :optional    => false,
          :maxlength   => 100

    input :packages,
          :prompt      => "Names of RPMs to be upgraded",
          :description => "Names of RPMs to be upgraded",
          :type        => :string,
          :validation  => /^.+$/,
          :optional    => false,
          :maxlength   => 800

    output :status,
           :description => "The output of the command",
           :display_as  => "Command result",
           :default     => "no output"
end

action "update_licence", :description => "Update Infoscale licence" do
    display :always

    output :status,
           :description => "The output of the command",
           :display_as  => "Command result",
           :default     => "no output"
end

action "remove_vrtsfsadv", :description => "Remove VRTSfsadv and reset vxfs_replication errors" do
    display :always

    output :retcode,
           :description => "The exit code from running the command",
           :display_as => "Result code"

    output :out,
           :description => "The stdout from running the command",
           :display_as => "out"

    output :err,
           :description => "The stderr from running the command",
           :display_as => "err"

end

action "disable_vxvm_boot", :description => "Disable vxvm-boot.service" do
    display :always

    output :status,
           :description => "The output of the command",
           :display_as  => "Command result",
           :default     => "no output"
end
