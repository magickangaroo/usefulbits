#!/usr/bin/python

# import modules
import MySQLdb, sys, smtplib, datetime, time

#Debugging levels, 4 shows all sql run, 3 shows all insert or updates.2 turns off sql debugging, and 1 shows notificational messages
#you want this at 1 during normal use to minimize the chattyness or 0 to turn off all output
DebuggingLevel=4

unixDate = int(time.mktime(time.localtime()))
db = MySQLdb.connect(host="localhost", user="viewer", passwd="rerjonyuc", db="postfixpolicyd")
cursor = db.cursor()

def sqlPrintAndExecute(SQL, DebugLevel=1, Message=''):
        cursor.execute(SQL)
        #so we want to check, if the passed DebugLevel is equal or less than the script default set above. 
        if DebuggingLevel>=DebugLevel:
                print "debug level = "+str(DebugLevel)+" i just ran the following sql: -"+str(SQL)
                if DebugLevel >= 1:
                        print "notification :- " + Message
        return cursor

sqlPrintAndExecute("select throttle._from as 'Ip Address', throttle._abuse_tot as 'Abuse Count' from throttle left join custom on custom.ipaddress = throttle._from where throttle._abuse_tot <> 0")

for exists in cursor.fetchall():

        sqlPrintAndExecute("select custom.ipaddress from custom where custom.ipaddress = '"+exists[0]+"'",4,"inital selection for comparision")
        results=cursor.fetchall()

        if cursor.rowcount == 0:

                #if were here, then we have a new spammer so lets update him into the custom database
                sqlPrintAndExecute("insert into custom values ('"+str(exists[0])+"',"+str(exists[1])+",1,"+str(unixDate)+",0)",3,"NEW SPAMMER ALERT :- ipaddress is "+str(exists[0]))

sqlPrintAndExecute("select throttle._from as 'Ip Address', throttle._abuse_tot as 'Abuse Count' from throttle left join custom on custom.ipaddress = throttle._from where throttle._abuse_tot <> 0 and custom.blacklisted != 1 order by throttle._abuse_tot Desc",4)

for record in cursor.fetchall():

        for match in results:
                sqlPrintAndExecute("select * from custom_comparison where custom_ip ='"+record[0]+"'",4)
                
                #if here then we have an ip which exists in both tables lets check if hes currently spamming
                #if he has a larger value in the abuse throttle than in the custom then he is.  putting this in a view for easy refernce

                                
                for spam in cursor.fetchall():
                #       print "adam Debuging   \n 1   "+str(spam[1])+"\n  2 "+str(spam[2])+"\n 3 "+str(spam[3])+"\n 4  "+str(spam[4])
                        #current hits is spam[2], custom abuse count is spam[1], thottle (live) count is spam[4]
                        #if custom count less than current (throttle account) then:
                        hits = spam[2]
                        hits += 1
                        print "This line : 1 is " +str(spam[1])+ " 2 is " +str(spam[2])+ " 3 is " +str(spam[3])+ " 4 is " +str(spam[4])+ " and unix date -450 is " + str(unixDate-450)
                        if spam[1] < spam[4] and spam[3]>unixDate-450:
                                #if were here, we have somone whos spamming, and has spamed previously within 450 secs.
                                print "do we get here??"
                                #if here we have somone whos currently spamming update date and current count
                                sqlPrintAndExecute("update custom set currentHits = "+str(hits)+", AbuseCount ="+str(spam[4])+",  date = "+str(unixDate)+" where ipaddress = '"+str(spam[0])+"'",3,"current spammer alert :- "+str(spam[0])
)

                                #ok so recent spammer, lets check if this is his limit (Currently 3 if so black list him)       
                                print "hits is " + str(hits)
                                if hits >= 4:
                                        sqlSuggestion = "insert into blacklist values ('"+str(spam[0])+"','automatic blacklist performed on "+datetime.datetime.now().strftime("%a %d/%m/%Y - %H:%M")+"',9999999999)"
                                        #turn off monitoring for this ip
                                        to = 'internalsystems@sohonet.co.uk'
                                        source = 'smtp.sohonet.co.uk@sohonet.co.uk'
                                        smtpserver = smtplib.SMTP("localhost", 25)
                                        smtpserver.ehlo()
                                        header = 'To:' + to + '\n' + 'From: ' + source + '\n' + 'Subject:Blacklisting alert for ip '+str(spam[0])+'\n'