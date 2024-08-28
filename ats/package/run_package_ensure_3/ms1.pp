
class task_ms1__litp_3a_3aversionlock__ms1(){
    litp::versionlock { "ms1":
excluded_packages => [

        ]

    }
}


node "ms1" {

    class {'litp::ms_node':}


    class {'task_ms1__litp_3a_3aversionlock__ms1':
    }


}