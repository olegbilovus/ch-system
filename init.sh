UTILITY=$PWD/chsystem/utility/
echo "$PYTHONPATH" | grep -q "$UTILITY"
if [ $? != 0 ]; then
  export PYTHONPATH=$PYTHONPATH:$UTILITY
  echo "Module $UTILITY added to $PYTHONPATH"
else
  echo "Module $UTILITY already present in $PYTHONPATH"
fi

DATABASE=$PWD/chsystem/database/
echo "$PYTHONPATH" | grep -q "$DATABASE"
if [ $? != 0 ]; then
  export PYTHONPATH=$PYTHONPATH:$DATABASE
  echo "Module $DATABASE added to $PYTHONPATH"
else
  echo "Module $DATABASE already present in $PYTHONPATH"
fi

echo "sleeping 15 secs..." && sleep 15

python3 "$1"
