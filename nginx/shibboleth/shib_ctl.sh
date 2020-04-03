#! /bin/sh


# Start. 
do_start () {
    /etc/init.d/shibd start
    sleep 1
    /etc/init.d/php7.3-fpm start
    sleep 1
    /etc/init.d/supervisor start
    sleep 1
    /etc/init.d/nginx reload
}

# Stop. 
do_stop () {
    /etc/init.d/shibd stop
    sleep 1
    /etc/init.d/php7.3-fpm stop
    sleep 1
    /etc/init.d/supervisor stop
}

# Status.
do_status () {
    /etc/init.d/shibd status
    sleep 1
    /etc/init.d/php7.3-fpm status
    sleep 1
    /etc/init.d/supervisor status
}



case "$1" in
start)
    do_start
    ;;
stop)
    do_stop
    ;;
restart)
    do_stop
    do_start
    ;;
status)
    do_status
    ;;
*)
    echo "Usage: $SCRIPTNAME {start|stop|restart|force-reload|status}" >&2
    exit 1
    ;;
esac

exit 0
