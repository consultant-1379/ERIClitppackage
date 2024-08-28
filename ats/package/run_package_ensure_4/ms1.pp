
class task_ms1__litp_3a_3aversionlock__ms1(){
    litp::versionlock { "ms1":
excluded_packages => [
        "0:pkg4-1.0-redhat1",
        "0:pkg3-1.0-1"
        ]

    }
}

class task_ms1__package__pkg1(){
    package { "pkg1":
        ensure => "installed",
        require => []
    }
}

class task_ms1__package__pkg2(){
    package { "pkg2":
        ensure => "latest",
        require => []
    }
}

class task_ms1__package__pkg3(){
    package { "pkg3":
        ensure => "1.0-1",
        require => []
    }
}

class task_ms1__package__pkg4(){
    package { "pkg4":
        ensure => "1.0-redhat1",
        require => []
    }
}


node "ms1" {

    class {'litp::ms_node':}


    class {'task_ms1__litp_3a_3aversionlock__ms1':
    }


    class {'task_ms1__package__pkg1':
    }


    class {'task_ms1__package__pkg2':
    }


    class {'task_ms1__package__pkg3':
    }


    class {'task_ms1__package__pkg4':
    }


}