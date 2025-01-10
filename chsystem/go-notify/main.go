package main

import (
	"fmt"
	log "github.com/sirupsen/logrus"
	"io"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"sync"
	"sync/atomic"
	"syscall"
	"time"
)

const (
	mimeJSON = "application/json"
	username = "Notifier"
)

func main() {
	var receivedSignal os.Signal
	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGTERM, syscall.SIGINT)

	db := Database{
		uri: os.Getenv("DB_URI"),
	}

	if err := db.setup(); err != nil {
		log.WithFields(log.Fields{
			"error": err.Error(),
		}).Fatalln("Error connecting to the db")
	}

	min5 := 5 * time.Minute
	for i := 1; receivedSignal == nil; receivedSignal, i = sleep(min5, sigs), i+1 {
		start := time.Now()
		log.Info("Started check #", i)

		clanNotifications, err := db.getNotifications()
		if err != nil {
			log.WithFields(log.Fields{
				"error": err.Error(),
			}).Errorln("Error getting clan notifications")
		}

		wg := sync.WaitGroup{}
		countNotif := atomic.Uint64{}
		for _, clanNotif := range clanNotifications {
			wg.Add(1)
			go func(notifications []*Notification, clanID int) {
				defer wg.Done()
				for _, notif := range notifications {

					subs := ""
					for _, sub := range notif.subs {
						subs += fmt.Sprintf("<@%d>", sub)
					}
					content := fmt.Sprintf("%s due in %s %s", notif.boss, minutesToDHM(timeRemainingMin(notif.timer)), subs)

					data := fmt.Sprintf(`{"username":"%s","content":"%s"}`, username, content)
					res, err := http.Post(notif.webhook, mimeJSON, strings.NewReader(data))
					if err != nil {
						log.WithFields(log.Fields{
							"error":  err.Error(),
							"clanID": clanID,
						}).Errorln("Error sending notification")
					} else {
						log.WithFields(log.Fields{
							"clanID":  clanID,
							"content": content,
						}).Infoln("Notification sent")
						countNotif.Add(1)
					}

					_, _ = io.Copy(io.Discard, res.Body)

				}
			}(clanNotif.notifications, clanNotif.clanID)
		}

		wg.Wait()

		log.WithFields(log.Fields{
			"duration":   time.Since(start),
			"countNotif": countNotif.Load(),
		}).Info("Finished check #", i)
	}

	log.Warn("Got signal ", receivedSignal)
	if err := db.close(); err != nil {
		log.WithFields(log.Fields{
			"error": err.Error(),
		}).Fatalln("Error closing the db")
	}
}

func sleep(duration time.Duration, sigChan <-chan os.Signal) os.Signal {
	select {
	case sig := <-sigChan:
		return sig
	case <-time.After(duration):
		return nil
	}
}
