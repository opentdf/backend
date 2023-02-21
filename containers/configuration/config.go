package main

import (
	"encoding/json"
	"log"
	"path/filepath"
    "os"
    "text/template"
)

const (
	ConfigDir    = "./global-configuration"
	ConfigFile   = "configuration.json"
	OutputDir    = "./app1-configuration"
	TemplateFile = "configuration.template"
)

type Config struct {
	Attributes     string `json:"attributes"`
	Entitlements   string `json:"entitlements"`
	Authority      string `json:"authority"`
	ClientId       string `json:"clientId"`
	Access         string `json:"access"`
	Realms         string `json:"realms"`
	BasePath       string `json:"basePath"`
}


func loadGlobalConfig() (*Config, error) {
	data := &Config{}
	dirPath, err := filepath.Abs(ConfigDir)
	if err != nil {
		return data, err
	}
	path := filepath.Join(dirPath, ConfigFile)

	file, err := os.Open(path)
	if err != nil {
		return data, err
	}

	decoder := json.NewDecoder(file)
	if err = decoder.Decode(&data); err != nil {
		return data, err
	}
	return data, nil
}


func saveAppConfig(cfg *Config) error {
	dirPath, err := filepath.Abs(OutputDir)
	if err != nil {
		return err
	}
	path := filepath.Join(dirPath, ConfigFile)

	file, err := os.Create(path)
	if err != nil {
		return err
	}
	defer file.Close()

	return json.NewEncoder(file).Encode(&cfg)
}

func saveAppConfigWithTemplate(cfg *Config) error {
	dirPath, err := filepath.Abs(OutputDir)
	if err != nil {
		return err
	}
	path := filepath.Join(dirPath, ConfigFile)
	file, err := os.Create(path)
	if err != nil {
		return err
	}
	defer file.Close()

	pathTemplate := filepath.Join(dirPath, TemplateFile)
	tmpl, err := template.ParseFiles(pathTemplate)
	if err != nil {
		return err
	}
	return tmpl.Execute(file, cfg)
}


func main() {
	configData, err := loadConfig()
	if err != nil {
		log.Fatal("error on parsing config: ", err)
	}

	err = saveAppConfig(configData)
	if err != nil {
		log.Fatal("error on writing config: ", err)
	}

	err = saveAppConfigWithTemplate(configData)
	if err != nil {
		log.Fatal("error on writing config: ", err)
	}

}