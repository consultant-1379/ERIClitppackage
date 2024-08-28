
class task_ms1__package__pkg(){
    package { "pkg":
        ensure => "absent"
    }
}


node "ms1" {

    class {'litp::ms_node':}


    class {'task_ms1__package__pkg':
    }


}