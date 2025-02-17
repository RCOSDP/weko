package main

import (
	"bytes"
	"embed"
	_ "embed"
	"github.com/alecthomas/chroma/formatters/html"
	"github.com/unrolled/render"
	"github.com/yuin/goldmark"
	highlighting "github.com/yuin/goldmark-highlighting"
	"html/template"
)

//### HTML
//go:embed pages
var pageAssets embed.FS

//### CSS
//go:embed assets
var embeddedAssets embed.FS

//### TEMPLATES
//go:embed templates/*
var templatesFS embed.FS

func initialiseRendering() {
	pageRender = render.New(render.Options{
		Directory: "templates",
		FileSystem: &render.EmbedFileSystem{
			FS: templatesFS,
		},
		Extensions: []string{".html"},
		Layout:     "_layout",
		IndentJSON: true,
	})
}

var markdownProcessor = goldmark.New(goldmark.WithExtensions(highlighting.NewHighlighting(highlighting.WithStyle("pygments"), highlighting.WithFormatOptions(html.TabWidth(2)))))

func GetHTMLFromMarkdown(pageBodyBytes []byte) (template.HTML, error) {
	var err error
	var pageBodyString template.HTML
	var buf bytes.Buffer
	err = markdownProcessor.Convert(pageBodyBytes, &buf)
	if err != nil {
		zapLogger.Error(err.Error())
		return pageBodyString, err
	}
	pageBodyString = template.HTML(buf.String())
	return pageBodyString, err
}
