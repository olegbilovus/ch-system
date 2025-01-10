package main

import (
	"fmt"
	"time"
)

func currTimeInMin() int64 {
	return time.Now().UTC().Unix() / 60
}

func timeRemainingMin(timer int) int64 {
	return int64(timer) - currTimeInMin()
}

func minutesToDHM(minutes int64) string {
	negative := false
	if minutes < 0 {
		minutes *= -1
		negative = true
	}

	days := minutes / 1440
	minutes %= 1440
	hours := minutes / 60
	minutes %= 60

	msg := ""
	if days > 0 {
		msg += fmt.Sprintf("%dd ", days)
	}
	if hours > 0 {
		msg += fmt.Sprintf("%dh ", hours)
	}
	msg += fmt.Sprintf("%dm", minutes)

	if negative {
		msg = "-" + msg
	}

	return msg
}
