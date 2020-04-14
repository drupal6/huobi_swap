ACTION=$1
CONFIG_PATH=$2
CONFIG_FILE=${CONFIG_PATH##*/}
MAIN_PATH=${CONFIG_FILE%%.*}
SERVER_ID=${MAIN_PATH}server.pid
OUT_FILE=${MAIN_PATH}.out
if [ -f `$SERVER_ID` ]
then
    PROCESS_ID=`/bin/cat $SERVER_ID`
    echo $PROCESS_ID
fi
case $ACTION in
    start)
    	if [ "$PROCESS_ID" ]
        then
            echo "${CONFIG_PATH} is started. processId:${PROCESS_ID}"
        else
            /usr/bin/nohup python main.py $CONFIG_PATH > $OUT_FILE &
            echo $! > $SERVER_ID
            PROCESS_ID=`/bin/cat $SERVER_ID`
            if [ "$PROCESS_ID" ]
            then
                echo "${CONFIG_PATH} started success. processId:${PROCESS_ID}"
            else
                echo "${CONFIG_PATH} start fail."
            fi          
    	fi
    ;;
    stop)
        if [ "$PROCESS_ID" ]
        then
            kill $PROCESS_ID
            /bin/rm -rf $SERVER_ID
            echo "${CONFIG_PATH} has killed."
        else
            echo "${CONFIG_PATH} is not running."
        fi
    ;;
    restart)
        if [ "$PROCESS_ID" ]
        then
            kill $PROCESS_ID
            /bin/rm -rf $SERVER_id
            echo "${CONFIG_PATH} has killed."
        fi
        /usr/bin/nohup python main.py CONFIG_PATH > $OUT_FILE &
        echo $! > $SERVER_ID
        PROCESS_ID=`/bin/cat $SERVER_ID`
        if [ "$PROCESS_ID" ]
        then
            echo "${CONFIG_PATH} started success. processId:$PROCESS_ID"
        else
            echo "${CONFIG_PATH} start fail."
        fi    
    ;;
    *)
    	echo "Usage:$0 (start|stop|restart) configpath"
esac
exit 0