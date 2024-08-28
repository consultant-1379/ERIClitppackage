metadata :name        => "dmp",
         :description => "Agent to handle DMP operations",
         :author      => "Ericsson AB",
         :license     => "Ericsson",
         :version     => "1.0",
         :url         => "http://ericsson.com",
         :timeout     => 600

action "dmp_config", :description => "Configure dmp" do
    display :always

    input :action,
          :prompt      => "Action name",
          :description => "Action name",
          :type        => :string,
          :validation  => '^(on|off)$',
          :optional    => false,
          :maxlength   => 3

    output :status,
           :description => "The output of the command",
           :display_as  => "Command result",
           :default     => "no output"
end

action "lvm_filter", :description => "Configure LVM global_filter" do
    display :always

    input :action,
          :prompt      => "Action name",
          :description => "Action name",
          :type        => :string,
          :validation  => '^(on|off)$',
          :optional    => false,
          :maxlength   => 3

    output :status,
           :description => "The output of the command",
           :display_as  => "Command result",
           :default     => "no output"
end

action "check_migrate_native_exists_and_remove", :description => "Check migrate_native file exists and removes it" do
    display :always

    output :status,
           :description => "The output of the command",
           :display_as  => "Command result",
           :default     => "no output"
end
