UTILITY=$PWD/chsystem/utility/
echo $PYTHONPATH | grep -q $UTILITY
if [ $? != 0 ]
then
    export PYTHONPATH=$PYTHONPATH:$UTILITY
else
    echo "Module $UTILITY already present in $PYTHONPATH"
fi

python3 $1