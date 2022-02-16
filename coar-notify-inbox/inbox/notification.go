package main

import (
	"encoding/json"
	"fmt"
	//"github.com/knakk/rdf"
	//"github.com/piprate/json-gold/ld"
	uuid "github.com/satori/go.uuid"
	"html/template"
	//"strings"
	"time"
)

type Notification struct {
	ID                 uuid.UUID `gorm:"type:uuid;primary_key;"`
	CreatedAt          time.Time
	UpdatedAt          time.Time
	DeletedAt          *time.Time `sql:"index"`
	Sender             string
	Payload            []byte
	//PayloadNQuads      string
	//PayloadTurtle      string
	ActivityId         string
	HttpRequest        string
	HttpResponseHeader string
	HttpResponseCode   int
	ProcessLog         string
	ValidRdf           bool
}

func NewNotification(sender string, timestamp time.Time) *Notification {

	var n Notification
	n.ID = uuid.NewV4()
	n.Sender = sender
	n.CreatedAt = timestamp
	return &n
}

func (notification *Notification) AddToProcessLog(message string) {
	notification.ProcessLog += message + "\n"
}

func (notification *Notification) ExpressPayloadAsInterface() (interface{}, error) {
	var err error
	var payloadInterface interface{}
	err = json.Unmarshal(notification.Payload, &(payloadInterface))
	if err != nil {
		zapLogger.Error(err.Error())
	}
	return payloadInterface, err
}

func (notification *Notification) Persist() { 
	db.Create(&notification)
}

func (notification *Notification) Url() string {
	return site.InboxUrl() + notification.ID.String()
}

func (notification *Notification) ProcessPayload() error {
	var err error
	payloadInterface, err := notification.ExpressPayloadAsInterface()
	if err != nil {
		return err
	}
	notification.Payload, _ = json.MarshalIndent(payloadInterface, "", "  ")
	payloadMap := payloadInterface.(map[string]interface{})
	notification.ActivityId = fmt.Sprintf("%v", payloadMap["id"])
	/*
	proc := ld.NewJsonLdProcessor()
	options := ld.NewJsonLdOptions("")
	options.Format = "application/n-quads"
	_, err = proc.Expand(payloadInterface, options)
	quads, err := proc.ToRDF(payloadInterface, options)
	if err != nil {
		zapLogger.Debug(err.Error())
		notification.AddToProcessLog(err.Error())
		return err
	}
	notification.PayloadNQuads = quads.(string)
	notification.AddToProcessLog("Appears to be valid JSON-LD")
	stringReader := strings.NewReader(notification.PayloadNQuads)
	decoder := rdf.NewTripleDecoder(stringReader, rdf.NTriples)
	triples, err := decoder.DecodeAll()
	if err != nil {
		zapLogger.Error(err.Error())
		return err
	}
	stringWriter := new(strings.Builder)
	encoder := rdf.NewTripleEncoder(stringWriter, rdf.Turtle)
	err = encoder.EncodeAll(triples)
	encoder.Close()
	notification.PayloadTurtle = stringWriter.String()
	if err != nil {
		zapLogger.Error(err.Error())
		return err
	}

	*/
	return err
}

func (notification *Notification) FormattedTimestamp() string {
	return notification.CreatedAt.Format("2006-01-02 15:04:05")
}
func (notification *Notification) HTMLFormattedPayload() template.HTML {
	if notification.ActivityId != "" {
		payloadJson := fmt.Sprintf("```json\n%s\n```\n", notification.Payload)
		htmlPayload, _ := GetHTMLFromMarkdown([]byte(payloadJson))
		return htmlPayload
	} else {
		htmlPayload, _ := GetHTMLFromMarkdown([]byte(notification.Payload))
		return htmlPayload
	}
}
/*
func (notification *Notification) HTMLFormattedPayloadNQuads() template.HTML {
	if notification.ActivityId != "" {
		payloadNQuads := fmt.Sprintf("```\n%s\n```\n", notification.PayloadNQuads)
		htmlPayload, _ := GetHTMLFromMarkdown([]byte(payloadNQuads))
		return htmlPayload
	} else {
		htmlPayload, _ := GetHTMLFromMarkdown([]byte(""))
		return htmlPayload
	}
}

func (notification *Notification) HTMLFormattedPayloadTurtle() template.HTML {
	if notification.ActivityId != "" {
		payloadTurtle := fmt.Sprintf("```turtle\n%s\n```\n", notification.PayloadTurtle)
		htmlPayload, _ := GetHTMLFromMarkdown([]byte(payloadTurtle))
		return htmlPayload
	} else {
		htmlPayload, _ := GetHTMLFromMarkdown([]byte(""))
		return htmlPayload
	}
}
*/
func (notification *Notification) HTMLFormattedHttpHeaders() template.HTML {
	markdown := "#### HTTP Request Headers\n"
	markdown += fmt.Sprintf("```yaml\n%s\n```\n", notification.HttpRequest)
	markdown += "#### HTTP Response Headers\n"
	markdown += fmt.Sprintf("```yaml\n%s\n```\n", notification.HttpResponseHeader)
	htmlPayload, _ := GetHTMLFromMarkdown([]byte(markdown))
	return htmlPayload
}
