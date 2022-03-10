package main

import "encoding/json"

const ldpContextURI = "http://www.w3.org/ns/ldp"

type Inbox struct {
	Notifications []Notification
}

func NewInbox(latest_get []string) Inbox {
	var i = Inbox{}
	i.Notifications = make([]Notification, 0) 
	if len(latest_get) == 0{
		zapLogger.Debug("find all")
		db.Find(&i.Notifications)
	}else{
		zapLogger.Debug("find some")
		db.Where("updated_at > ?", latest_get[0]).Find(&i.Notifications)
	}
	return i
}

func (inbox *Inbox) GetAsMap() map[string]interface{} {

	inboxPayload := make(map[string]interface{})
	notificationURIs := make([]string, 0)
	for _, notification := range inbox.Notifications { 
		notificationURIs = append(notificationURIs, notification.Url())
	}
	inboxPayload["@context"] = ldpContextURI
	inboxPayload["@id"] = site.InboxUrl()
	inboxPayload["contains"] = notificationURIs
	return inboxPayload
}

func (inbox *Inbox) GetAsString() string {

	var jsonString string
	jsonMap := inbox.GetAsMap()
	bytes, err := json.Marshal(jsonMap)
	if err == nil {
		jsonString = string(bytes)
	}
	return jsonString
}
