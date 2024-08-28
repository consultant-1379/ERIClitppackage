
class task_node1__litp_3a_3aversionlock__node1(){
    litp::versionlock { "node1":
excluded_packages => [

        ]

    }
}

class task_node1__package__file(){
    package { "file":
        ensure => "installed",
        require => []
    }
}

class task_node1__package__vim_2denhanced(){
    package { "vim-enhanced":
        ensure => "installed",
        require => []
    }
}


node "node1" {

    class {'litp::mn_node':
        ms_hostname => "ms1",
        cluster_type => "NON-CMW"
        }


    class {'task_node1__litp_3a_3aversionlock__node1':
    }


    class {'task_node1__package__file':
    }


    class {'task_node1__package__vim_2denhanced':
    }


}