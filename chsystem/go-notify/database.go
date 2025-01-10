package main

import (
	"database/sql"
	_ "github.com/lib/pq"
)

const (
	sqlClanDiscord = `SELECT clanid, notifywebhook FROM clandiscord  WHERE notifywebhook IS NOT NULL`
	sqlNotifyData  = `SELECT id, timer, bossname FROM timer WHERE clanid = $1 AND timer >= $2 AND timer <= $3`
	sqlTimerSubs   = `SELECT discordid FROM subscriber, discordid WHERE timerid = $1 AND subscriber.userprofileid = discordid.userprofileid`
)

type Database struct {
	uri string
	db  *sql.DB
}

func (d *Database) setup() error {
	var err error
	d.db, err = sql.Open("postgres", d.uri)
	if err == nil {
		return d.db.Ping()
	}
	return err
}

func (d *Database) close() error {
	return d.db.Close()
}

type Notification struct {
	webhook string
	boss    string
	timer   int
	subs    []int
}

type ClanNotifications struct {
	clanID        int
	notifications []*Notification
}

func (d *Database) getNotifications() ([]ClanNotifications, error) {
	clanNotifications := make([]ClanNotifications, 0)

	clansDiscord, err := d.db.Query(sqlClanDiscord)
	if err != nil {
		return nil, err
	}

	for clansDiscord.Next() {
		var clanID int
		var webhook string
		err := clansDiscord.Scan(&clanID, &webhook)
		if err != nil {
			return nil, err
		}

		clanNotif := ClanNotifications{
			clanID:        clanID,
			notifications: make([]*Notification, 0),
		}

		nowMin := currTimeInMin()
		timers, err := d.db.Query(sqlNotifyData, clanID, nowMin, nowMin+10)
		if err != nil {
			return nil, err
		}
		for timers.Next() {
			var timerID, timer int
			var bossname string
			err := timers.Scan(&timerID, &timer, &bossname)
			if err != nil {
				return nil, err
			}

			timerSubs, err := d.db.Query(sqlTimerSubs, timerID)
			if err != nil {
				return nil, err
			}

			notification := &Notification{
				webhook: webhook,
				boss:    bossname,
				timer:   timer,
				subs:    make([]int, 0),
			}

			for timerSubs.Next() {
				var subDiscordID int
				err := timerSubs.Scan(&subDiscordID)
				if err != nil {
					return nil, err
				}
				notification.subs = append(notification.subs, subDiscordID)
			}

			clanNotif.notifications = append(clanNotif.notifications, notification)
		}

		clanNotifications = append(clanNotifications, clanNotif)
	}

	return clanNotifications, nil

}
