define package::replace_script($replacement, $replaced, $uname, $script){

    exec { "replace_$uname" :
        path     => "/bin/:/usr/bin:",
        provider => "shell",
        onlyif  => ["! rpm -q $replacement", "yum list $replacement"],
        command => "rpm -e --nodeps -- $replaced 2>/dev/null; yum install -y -- $replacement",
        notify => Exec["check_result_$uname"]
    }

    exec { "check_result_$uname" :
        path     => "/bin/:/usr/bin:",
        provider => "shell",
        command  => "rpm -q $replacement && ! rpm -q $replaced"
    }

}