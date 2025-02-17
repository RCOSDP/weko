package main

import (
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
	"strconv"
	"github.com/kelseyhightower/envconfig"
)

type Config struct {
	Debugging      bool
	Port           int
	DbFilePath     string
	DbSaveInterval string
}

type GlobalConfig struct {
	Db_path string 
	Host string
	Debug bool
	Port int
}

var site = Site{}

func (config *Config) initialise() {
	var goenv GlobalConfig
	envconfig.Process("notify_ldn_inbox", &goenv)
	config.Debugging = goenv.Debug
	zapLogger, _ = configureZapLogger(config.Debugging)
	if config.Debugging == true {
		zapLogger.Info("Debugging enabled")
	}
	config.Port = goenv.Port
	zapLogger.Debug("Set port to ", zap.Int("port", config.Port))
	if config.Port == 80 {
		site.BaseUrl = "https://"+goenv.Host
	} else {
		site.BaseUrl = "https://"+goenv.Host+":" + strconv.Itoa(config.Port)
	}
	zapLogger.Debug("Set base url to ", zap.String("host", site.BaseUrl))
	config.DbFilePath = goenv.Db_path
	zapLogger.Debug("Set db path to ", zap.String("db path", config.DbFilePath))
}

func configureZapLogger(debugging bool) (*zap.Logger, error) {
	level := zapcore.InfoLevel
	encoderConfig := zapcore.EncoderConfig{
		MessageKey:  "message",
		LevelKey:    "level",
		TimeKey:     "",
		EncodeLevel: zapcore.CapitalColorLevelEncoder,
	}
	if debugging == true {
		level = zapcore.DebugLevel
		encoderConfig = zapcore.EncoderConfig{
			MessageKey:   "message",
			LevelKey:     "level",
			TimeKey:      "",
			EncodeLevel:  zapcore.CapitalColorLevelEncoder,
			CallerKey:    "caller",
			EncodeCaller: zapcore.ShortCallerEncoder,
		}
	}
	zapConfig := zap.Config{
		Encoding:      "console",
		Level:         zap.NewAtomicLevelAt(level),
		OutputPaths:   []string{"stdout"},
		EncoderConfig: encoderConfig,
	}
	return zapConfig.Build()
}

func configure() error {
	var err error
	config.initialise()
	if config.DbFilePath != "" {
		err = InitialiseDb(config.DbFilePath)
		if err != nil {
			zapLogger.Error(err.Error())
			return err
		}
	}
	initialiseRendering()
	router = ConfigureRouter()
	return err
}
