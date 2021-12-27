UTILITY=$PWD/chsystem/utility/
DATABASE=$PWD/chsystem/database/

echo $PYTHONPATH | grep -q $UTILITY
if [ $? != 0 ]
then
    export PYTHONPATH=$PYTHONPATH:$UTILITY
else
    echo "Module $UTILITY already present in $PYTHONPATH"
fi

echo $PYTHONPATH | grep -q $DATABASE
if [ $? != 0 ]
then
    export PYTHONPATH=$PYTHONPATH:$DATABASE
else
    echo "Module $DATABASE already present in $PYTHONPATH"
fi

python3 $1