

ACTION=$1
PYTHON_SCRIPT=$2
MAIN_PATH=${PYTHON_SCRIPT%%.*}
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
            echo "${PYTHON_SCRIPT} is started. processId:${PROCESS_ID}"
        else
            /usr/bin/nohup python $PYTHON_SCRIPT > $OUT_FILE &
            echo $! > $SERVER_ID
            PROCESS_ID=`/bin/cat $SERVER_ID`
            if [ "$PROCESS_ID" ]
            then
                echo "${PYTHON_SCRIPT} started success. processId:${PROCESS_ID}"
            else
                echo "${PYTHON_SCRIPT} start fail."
            fi          
    	fi
    ;;
    stop)
        if [ "$PROCESS_ID" ]
        then
            kill $PROCESS_ID
            /bin/rm -rf $SERVER_ID
            echo "${PYTHON_SCRIPT} has killed."
        else
            echo "${PYTHON_SCRIPT} is not running."
        fi
    ;;
    restart)
        if [ "$PROCESS_ID" ]
        then
            kill $PROCESS_ID
            /bin/rm -rf $SERVER_id
            echo "${PYTHON_SCRIPT} has killed."
        fi
        /usr/bin/nohup python $PYTHON_SCRIPT > $OUT_FILE &
        echo $! > $SERVER_ID
        PROCESS_ID=`/bin/cat $SERVER_ID`
        if [ "$PROCESS_ID" ]
        then
            echo "${PYTHON_SCRIPT} started success. processId:$PROCESS_ID"
        else
            echo "${PYTHON_SCRIPT} start fail."
        fi    
    ;;
    *)
    	echo "Usage:$0 (start|stop|restart) pyscript"
esac
exit 0
