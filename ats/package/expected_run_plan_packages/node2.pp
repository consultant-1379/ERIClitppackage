
class task_node2__litp_3a_3aversionlock__node2(){
    litp::versionlock { "node2":
excluded_packages => [

        ]

    }
}

class task_node2__package__file(){
    package { "file":
        ensure => "installed",
        require => []
    }
}

class task_node2__package__vim_2denhanced(){
    package { "vim-enhanced":
        ensure => "installed",
        require => []
    }
}


node "node2" {

    class {'litp::mn_node':
        ms_hostname => "ms1",
        cluster_type => "NON-CMW"
        }


    class {'task_node2__litp_3a_3aversionlock__node2':
    }


    class {'task_node2__package__file':
    }


    class {'task_node2__package__vim_2denhanced':
    }


}