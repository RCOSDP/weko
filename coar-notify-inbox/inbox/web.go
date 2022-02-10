package main

import "html/template"

type Site struct {
	BaseUrl string
}

func (site *Site) InboxUrl() string {
	return site.BaseUrl + "/inbox/"
}

type Page struct {
	Title  string
	Body   template.HTML
	Params map[string]interface{}
	Site   Site
}

type InboxPage struct {
	Page
	Notifications []Notification
}

type NotificationPage struct {
	Page
	Notification Notification
}

func NewInboxPage(notifications []Notification) *InboxPage {
	var p InboxPage
	p.Page = *NewPage()
	p.Notifications = notifications
	return &p
}

func NewNotificationPage(notification Notification) *NotificationPage {
	var p NotificationPage
	p.Page = *NewPage()
	p.Notification = notification
	return &p
}

func NewPage() *Page {
	var p Page
	p.Params = make(map[string]interface{})
	p.Site = site
	return &p
}
