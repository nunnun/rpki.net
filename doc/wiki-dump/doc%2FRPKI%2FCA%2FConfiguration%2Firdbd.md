# [irdbd] section

irdbd's default configuration file is the system `rpki.conf` file. Start irdbd
with "`-c filename`" to choose a different configuration file. All options are
in the "`[irdbd]`" section.

Since irdbd is part of the back-end system, it has direct access to the back-
end's SQL database, and thus is able to pull its own BPKI configuration
directly from the database, and thus needs a bit less configuration than the
other daemons.

## sql-database

MySQL database name for irdbd.

    
    
    sql-database = ${myrpki::irdbd_sql_database}
    

## sql-username

MySQL user name for irdbd.

    
    
    sql-username = ${myrpki::irdbd_sql_username}
    

## sql-password

MySQL password for irdbd.

    
    
    sql-password = ${myrpki::irdbd_sql_password}
    

## server-host

Host on which irdbd should listen for HTTP service requests.

    
    
    server-host = ${myrpki::irdbd_server_host}
    

## server-port

Port on which irdbd should listen for HTTP service requests.

    
    
    server-port = ${myrpki::irdbd_server_port}
    

## startup-message

String to log on startup, useful when debugging a collection of irdbd
instances at once.

No default value.

