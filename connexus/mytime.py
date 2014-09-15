from datetime import datetime

def olderthanhour(checktimestring):
  nowstring = str(datetime.now())
  splitstring = nowstring.split(' ')
  date = splitstring[0]
  time = splitstring[1]
  date = date.split('-')
  currentyear = int(date[0])
  currentmonth = int(date[1])
  currentday = int(date[2])
  time = time.split(':')
  currenthour = int(time[0])
  currentminute = int(time[1])
  time = time[2].split('.')
  currentsecond = int(time[0])
  timestring = str(currentyear) + ' ' + str(currentmonth) + ' ' + str(currentday) + ' ' + str(currenthour) + ' ' + str(currentminute) + ' ' + str(currentsecond)
  print('Times found: ' + timestring + '\n')
  splitstring = checktimestring.split(' ')
  date = splitstring[0]
  time = splitstring[1]
  date = date.split('-')
  checkyear = int(date[0])
  checkmonth = int(date[1])
  checkday = int(date[2])
  time = time.split(':')
  checkhour = int(time[0])
  checkminute = int(time[1])
  time = time[2].split('.')
  checksecond = int(time[0])
  newtimestring = str(checkyear) + ' ' + str(checkmonth) + ' ' + str(checkday) + ' ' + str(checkhour) + ' ' + str(checkminute) + ' ' + str(checksecond)
  print('Check times found: ' + newtimestring)

time1 = str(datetime.now())
y = 1
for x in range(0,100000):
  y = y * x + 1
olderthanhour(time1)