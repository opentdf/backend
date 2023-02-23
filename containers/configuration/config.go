package main

import (
	"gopkg.in/yaml.v3"
	"log"
	"path/filepath"
    "os"
    "text/template"
)

const (
	ConfigDir    = "./global-configuration"
	ConfigFile   = "configuration.yaml"
	OutputDir    = "./app1-configuration"
	TemplateFile = "configuration.template"
)

type Config struct {
	Attributes     string `yaml:"attributes"`
	Entitlements   string `yaml:"entitlements"`
	Authority      string `yaml:"authority"`
	ClientId       string `yaml:"clientId"`
	Access         string `yaml:"access"`
	Realms         string `yaml:"realms"`
	BasePath       string `yaml:"basePath"`
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

	decoder := yaml.NewDecoder(file)
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

	return yaml.NewEncoder(file).Encode(&cfg)
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
	configData, err := loadGlobalConfig()
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