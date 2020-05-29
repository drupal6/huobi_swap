ACTION=$1
CONFIG_PATH=$2
CONFIG_FILE=${CONFIG_PATH##*/}
MAIN_PATH=${CONFIG_FILE%%.*}
OUT_FILE=${MAIN_PATH}.out

COMMAND_STR="python main.py $CONFIG_PATH"
ID=`ps -ef | grep "$COMMAND_STR" | grep -v "grep" | awk '{print $2}'`

case $ACTION in
    start)
    	if [ "$ID" ]
        then
            echo "start fail. ${CONFIG_PATH} is started. processId:${ID}"
        else
            /usr/bin/nohup python main.py $CONFIG_PATH > $OUT_FILE &
            ID=$!
            if [ "$ID" ]
            then
                echo "${CONFIG_PATH} started success. processId:${ID}"
            else
                echo "${CONFIG_PATH} start fail."
            fi          
    	fi
    ;;
    stop)
        if [ "$ID" ]
        then
            kill $ID
            echo "${CONFIG_PATH} has killed."
        else
            echo "${CONFIG_PATH} is not running."
        fi
    ;;
    restart)
        if [ "$ID" ]
        then
            kill $PROCESS_ID
            echo "${CONFIG_PATH} has killed."
        fi
        /usr/bin/nohup python main.py CONFIG_PATH > $OUT_FILE &
        ID=$!
        if [ "$ID" ]
        then
            echo "${CONFIG_PATH} started success. processId:$ID"
        else
            echo "${CONFIG_PATH} start fail."
        fi    
    ;;
    *)
    	echo "Usage:$0 (start|stop|restart) configpath"
esac
exit 0
