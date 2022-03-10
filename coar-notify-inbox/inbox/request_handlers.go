package main

import (
	"fmt"
	_ "github.com/alecthomas/chroma/formatters"
	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	uuid "github.com/satori/go.uuid"
	"gopkg.in/yaml.v2"
	"io/ioutil"
	"net/http"
	"path/filepath"
	"time"
)

func Options(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Allow", "GET, HEAD, OPTIONS, POST") 
	w.Header().Set("Accept-Post", "application/ld+json")
	pageRender.Text(w, http.StatusOK, "")
}

func HomePageGet(w http.ResponseWriter, r *http.Request) {

	var page = NewPage()
	page.Title = "Home"
	pageBytes, _ := GetPageBodyAsByteSliceFromFs("home.md")
	html, _ := GetHTMLFromMarkdown(pageBytes)
	page.Body = html
	pageRender.HTML(w, http.StatusOK, "page", page)
}

func InboxPost(w http.ResponseWriter, r *http.Request) {

	var err error
	notification := NewNotification(GetIP(r), time.Now())
	requestHeaderAsBytes, _ := yaml.Marshal(r.Header)
	notification.HttpRequest = string(requestHeaderAsBytes)
	payloadJson, err := ioutil.ReadAll(r.Body)
	if handlePostErrorCondition(err, w, 400, "Unable to read posted content", notification) {
		return
	}
	notification.Payload = payloadJson
	err = notification.ProcessPayload()
	if handlePostErrorCondition(err, w, 400, "Unable to parse posted content (must be JSON-LD)", notification) {
		return
	}
	var page = NewPage() 
	page.Params["notificationUrl"] = fmt.Sprint(notification.ID)
	page.Title = "Notification Response"
	w.Header().Set("Location", notification.Url())
	err = pageRender.HTML(w, http.StatusCreated, "post_success", page)
	if handlePostErrorCondition(err, w, 500, "Unable to process request", notification) {
		return
	}
	notification.HttpResponseCode = 201
	responseHeaderAsBytes, _ := yaml.Marshal(w.Header())
	notification.HttpResponseHeader = string(responseHeaderAsBytes)
	notification.Persist()
}

func handlePostErrorCondition(err error, w http.ResponseWriter, code int, message string, notification *Notification) bool {
	if err != nil {
		zapLogger.Error(err.Error())
		http.Error(w, message, code)
		notification.HttpResponseCode = code
		responseHeaderAsBytes, _ := yaml.Marshal(w.Header())
		notification.HttpResponseHeader = string(responseHeaderAsBytes)
		notification.Persist()
		return true
	} else {
		return false
	}
}

func InboxGet(w http.ResponseWriter, r *http.Request) {
	zapLogger.Debug(fmt.Sprint(r.Header))
	latest_get := r.Header["Latestget"]
	inbox := NewInbox(latest_get)
	if CheckExistenceAcceptHeaderMimeValue(r, "application/ld+json") {//ヘッダーのAcceptの値にapplication/ld+jsonはある？
		w.Header().Set("Content-Type", "application/ld+json")
		pageRender.Text(w, http.StatusOK, inbox.GetAsString())
	} else if CheckExistenceAcceptHeaderMimeValue(r, "application/json") {//ヘッダーのAcceptの値にapplication/jsonはある？
		w.Header().Set("Content-Type", "application/json")
		pageRender.Text(w, http.StatusOK, inbox.GetAsString())
	} else {
		page := NewInboxPage(inbox.Notifications)
		page.Title = "Inbox"
		pageRender.HTML(w, http.StatusOK, "inbox", page)
	}
}

//func InboxGetJSON(w http.ResponseWriter, r *http.Request) {
//	inbox := NewInbox()
//	w.Header().Set("Content-Type", "application/ld+json")
//	pageRender.JSON(w, http.StatusOK, inbox.GetAsMap())
//}

func InboxNotificationGet(w http.ResponseWriter, r *http.Request) {
	urlFormat, _ := r.Context().Value(middleware.URLFormatCtxKey).(string)//urlの拡張子を取得
	if urlFormat == "" {
		urlFormat = GetFirstAcceptedMimeValue(r)
	}
	if urlFormat == "" {
		urlFormat = "html"
	}
	idString := chi.URLParam(r, "id")
	id, _ := uuid.FromString(idString)
	notification := Notification{}
	db.First(&notification, id) 
	switch urlFormat {
	case "application/ld+json", "application/json", "json":
		if notification.ActivityId != "" {
			w.Header().Set("Content-Type", "application/ld+json")
			pageRender.Text(w, http.StatusOK, string(notification.Payload))//ペイロードの出力
		} else {
			http.Error(w, "No RDF representation of this resource was found", 404)
		}
/*
	case "application/n-quads", "nq":
		if notification.ActivityId != "" {
			w.Header().Set("Content-Type", "application/n-quads")
			pageRender.Text(w, http.StatusOK, string(notification.PayloadNQuads))
		} else {
			http.Error(w, "No RDF representation of this resource was found", 404)
		}
	case "text/turtle", "ttl":
		if notification.ActivityId != "" {
			w.Header().Set("Content-Type", "text/turtle")
			pageRender.Text(w, http.StatusOK, string(notification.PayloadTurtle))
		} else {
			http.Error(w, "No RDF representation of this resource was found", 404)
		}
*/
	default:
		var page = NewNotificationPage(notification)
		page.Title = "Notification"
		pageRender.HTML(w, http.StatusOK, "notification", page)
	}
}

func InboxNotificationDelete(w http.ResponseWriter, r *http.Request) {
	idString := chi.URLParam(r, "id")
	id, _ := uuid.FromString(idString)
	notification := Notification{}
	db.Delete(&notification, id)
	pageRender.Text(w, http.StatusOK, "delete :id=" + idString)
}

func GetPageBodyAsByteSliceFromFs(filename string) ([]byte, error) {
	var err error
	pageBodyBytes, err := pageAssets.ReadFile(filepath.Join("pages", filename))
	return pageBodyBytes, err
}

func GetIP(r *http.Request) string {
	IPAddress := r.Header.Get("X-Real-Ip")
	if IPAddress == "" {
		IPAddress = r.Header.Get("X-Forwarded-For")
	}
	if IPAddress == "" {
		IPAddress = r.RemoteAddr
	}
	return IPAddress
}

func CheckExistenceAcceptHeaderMimeValue(r *http.Request, mime string) bool {
	for _, v := range r.Header.Values("Accept") {
		if v == mime {
			return true
		}
	}
	return false
}

func GetFirstAcceptedMimeValue(r *http.Request) string {
	for _, v := range r.Header.Values("Accept") {
		return v
	}
	return ""
}
