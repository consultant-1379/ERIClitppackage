
class task_ms1__litp_3a_3aversionlock__ms1(){
    litp::versionlock { "ms1":
excluded_packages => [

        ]

    }
}

class task_ms1__package__pkg(){
    package { "pkg":
        ensure => "installed",
        require => []
    }
}


node "ms1" {

    class {'litp::ms_node':}


    class {'task_ms1__litp_3a_3aversionlock__ms1':
    }


    class {'task_ms1__package__pkg':
    }


}