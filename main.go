package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/bwmarrin/discordgo"
	"github.com/joho/godotenv"
	"github.com/matthewyuh246/hackathon/models"
	"github.com/robfig/cron"
	"golang.org/x/oauth2"
	"golang.org/x/oauth2/google"
	"google.golang.org/api/calendar/v3"
	"google.golang.org/api/option"
)

var events []models.Event
var c = cron.New()

func loadEnv() {
	err := godotenv.Load(".env")

	if err != nil {
		fmt.Println(".env読み込みエラー: %v", err)
	}
	fmt.Println(".envを読み込みました。")
}

func messageCreate(s *discordgo.Session, m *discordgo.MessageCreate) {
	if m.Author.ID == s.State.User.ID {
		return
	}

	if m.Content[:4] == "!add" {
		parts := strings.TrimSpace(m.Content[5:])
		details := strings.SplitN(parts, "|", 2)

		if len(details) != 2 {
			s.ChannelMessageSend(m.ChannelID, "形式: !add <YYYY-MM-DD HH:MM>|<予定タイトル>")
			return
		}
		fmt.Println("Received date string:", details[0]) // デバッグ用出力

		eventTime, err := time.Parse("2006-01-02 15:04", details[0])
		if err != nil {
			s.ChannelMessageSend(m.ChannelID, "日付形式が無効です。例: 2024-12-31 13:00")
			fmt.Println("Date parsing error:", err) // エラーの内容を出力
			return
		}

		event := models.Event{
			Title:     details[1],
			Time:      eventTime,
			ChannelID: m.ChannelID,
		}
		events = append(events, event)

		scheduleReminders(s, event)
		s.ChannelMessageSend(m.ChannelID, "予定を追加しました: "+details[1])
		s.ChannelMessageSend(m.ChannelID, fmt.Sprintf("%s は %s です。", details[1], eventTime.Format("2006-01-02 15:04")))
	}
}

func scheduleReminders(s *discordgo.Session, event models.Event) {
	reminderTime36 := event.Time.Add(-36 * time.Hour)
	c.AddFunc(reminderTime36.Format("05 04 15 02 01 *"), func() {
		sendReminder(s, event.ChannelID, event.Title, 36)
	})

	reminderTime12 := event.Time.Add(-12 * time.Hour)
	c.AddFunc(reminderTime12.Format("05 04 15 02 01 *"), func() {
		sendReminder(s, event.ChannelID, event.Title, 12)
	})
}

func sendReminder(s *discordgo.Session, channelID, title string, hours int) {
	s.ChannelMessageSend(channelID, fmt.Sprintf("%sが%d時間後にあります！", title, hours))
}

// Google Calendarの認証とクライアントのセットアップ
func getClient() (*calendar.Service, error) {
	b, err := os.ReadFile("credentials.json")
	if err != nil {
		log.Fatalf("Unable to read client secret file: %v", err)
	}

	config, err := google.ConfigFromJSON(b, calendar.CalendarReadonlyScope)
	if err != nil {
		log.Fatalf("Unable to parse client secret file to config: %v", err)
	}

	tokFile := "token.json"
	tok, err := tokenFromFile(tokFile)
	if err != nil {
		tok = getTokenFromWeb(config)
		saveToken(tokFile, tok)
	}
	client := config.Client(context.Background(), tok)
	return calendar.NewService(context.Background(), option.WithHTTPClient(client))
}

// DiscordにGoogleカレンダーイベントを通知する関数
func notifyDiscord(s *discordgo.Session, calendarService *calendar.Service, calendarID string, channelID string) {
	events, err := calendarService.Events.List(calendarID).ShowDeleted(false).
		SingleEvents(true).TimeMin(time.Now().Format(time.RFC3339)).MaxResults(10).OrderBy("startTime").Do()
	if err != nil {
		log.Fatalf("Unable to retrieve events. %v", err)
	}

	if len(events.Items) == 0 {
		s.ChannelMessageSend(channelID, "Upcoming events not found.")
		return
	}

	for _, item := range events.Items {
		var start string
		if item.Start.DateTime != "" {
			start = item.Start.DateTime
		} else {
			start = item.Start.Date
		}
		message := fmt.Sprintf("Event: %s\nStart: %s\nLink: %s", item.Summary, start, item.HtmlLink)
		s.ChannelMessageSend(channelID, message)
	}
}

func tokenFromFile(file string) (*oauth2.Token, error) {
	f, err := os.Open(file)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	tok := &oauth2.Token{}
	err = json.NewDecoder(f).Decode(tok)
	return tok, err
}

func saveToken(path string, token *oauth2.Token) {
	f, err := os.Create(path)
	if err != nil {
		log.Fatalf("Unable to cache oauth token: %v", err)
	}
	defer f.Close()
	json.NewEncoder(f).Encode(token)
}

func getTokenFromWeb(config *oauth2.Config) *oauth2.Token {
	authURL := config.AuthCodeURL("state-token", oauth2.AccessTypeOffline)
	fmt.Printf("Go to the following link in your browser then type the authorization code: \n%v\n", authURL)

	var authCode string
	if _, err := fmt.Scan(&authCode); err != nil {
		log.Fatalf("Unable to read authorization code %v", err)
	}

	tok, err := config.Exchange(context.TODO(), authCode)
	if err != nil {
		log.Fatalf("Unable to retrieve token from web %v", err)
	}
	return tok
}

func main() {
	loadEnv()
	// Discord Botの初期化
	discordToken := os.Getenv("DISCORD_BOT_TOKEN")
	channelID := os.Getenv("DISCORD_CHANNEL_ID") // DiscordチャンネルID
	dg, err := discordgo.New("Bot " + discordToken)
	if err != nil {
		log.Fatalf("Error creating Discord session: %v", err)
	}
	defer dg.Close()

	// Google Calendar APIクライアントのセットアップ
	calendarService, err := getClient()
	if err != nil {
		log.Fatalf("Error creating Calendar client: %v", err)
	}

	calendarID := "primary"

	// Discordで "!events" コマンドが実行されたらGoogleカレンダーからイベントを取得して通知
	dg.AddHandler(func(s *discordgo.Session, m *discordgo.MessageCreate) {
		if m.Author.ID == s.State.User.ID {
			return
		}
		if m.Content == "!events" {
			notifyDiscord(s, calendarService, calendarID, channelID)
		}
	})

	dg.AddHandler(messageCreate)

	err = dg.Open()
	if err != nil {
		log.Fatalf("Error opening Discord session: %v", err)
	}
	defer dg.Close()
	fmt.Println("Bot稼働中。CTRL+Cで終了。")

	c.Start()
	defer c.Stop()

	sc := make(chan os.Signal, 1)
	signal.Notify(sc, syscall.SIGINT, syscall.SIGTERM, os.Interrupt)
	<-sc
}
