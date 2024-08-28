metadata :name        => "yum",
         :description => "Agent to handle yum operations",
         :author      => "Ericsson AB",
         :license     => "Ericsson",
         :version     => "1.0",
         :url         => "http://ericsson.com",
         :timeout     => 1800

action "get_packages", :description => "Query yum to get the list of packages to upgrade" do
    display :always

    output :status,
           :description => "The output of the command, including the packages",
           :display_as  => "Command result",
           :default     => "no output"
end

action "get_all_packages", :description => "Query yum to get the list of packages to upgrade from all repos" do
    display :always

    output :status,
           :description => "The output of the command, including the packages",
           :display_as  => "Command result",
           :default     => "no output"
end

action "upgrade_package", :description => "Upgrade a package" do
    display :always

    input :name,
          :prompt      => "Package name",
          :description => "Package name",
          :type        => :string,
          :validation  => '^((\w|\.|\+)*-)*(\w|\.|\+)+(\s((\w|\.|\+)*-)*(\w|\.|\+)+)?',
          :optional    => false,
          :maxlength   => 100

    output :status,
           :description => "The output of the command",
           :display_as  => "Command result",
           :default     => "no output"
end

action "upgrade_all_packages", :description => "Upgrade all packages" do
    display :always

    output :status,
           :description => "The output of the command",
           :display_as  => "Command result",
           :default     => "no output"
end

action "complete_transaction", :description => "Complete a pending transaction" do
    display :always

    output :status,
           :description => "The output of the command",
           :display_as  => "Command result",
           :default     => "no output"
end

action "set_state_vcs_services", :description => "Set the state of VCS services" do
    display :always

    input :commands_str,
          :prompt      => "Commands",
          :description => "VCS commands string, semi-colon separated",
          :type        => :string,
          :validation  => /^.+$/,
          :optional    => false,
          :maxlength   => 0

    output :status,
           :description => "The output of the commands",
           :display_as  => "Commands result",
           :default     => "no output"
end

action "vcs_status", :description => "Get the status of VCS" do
    display :always

    output :status,
           :description => "The output of the hastatus -sum command",
           :display_as  => "Command result",
           :default     => "no output"
end

action "replace_package", :description => "Replace an RPM with another" do
    display :always

    input :replacement,
          :prompt      => "Replacement RPM name",
          :description => "Replacement RPM name",
          :type        => :string,
          :validation  => '^((\w|\.|\+)*-)*(\w|\.|\+)+$',
          :optional    => false,
          :maxlength   => 100

    input :replaced,
          :prompt      => "Replaced RPM name",
          :description => "Replaced RPM name",
          :type        => :string,
          :validation  => '^((\w|\.|\+)*-)*(\w|\.|\+)+$',
          :optional    => false,
          :maxlength   => 100

    output :status,
           :description => "The output of the commands",
           :display_as  => "Commands result",
           :default     => "no output"
end
