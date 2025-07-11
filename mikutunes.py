#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, GObject, Gst, GLib, GdkPixbuf, Gdk
import os
import random
import sys

# Initialize GStreamer
Gst.init(None)

class MikuTunesPlayer(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="MikuTunes")
        
        # Song database
        self.miku_bangers = [
            {
                "title": "Tell Your World",
                "creator": "livetune",
                "genre": "Electropop",
                "file": "tellyourworld.mp3",
                "cover": "tellyourworld.png"
            },
            {
                "title": "The Disappearance of Hatsune Miku",
                "creator": "cosMo@Bousou-P",
                "genre": "Speedcore / Vocaloid Rock",
                "file": "thedisappearanceofhatsunemiku.mp3",
                "cover": "thedisappearanceofhatsunemiku.png"
            },
            {
                "title": "World is Mine",
                "creator": "ryo (supercell)",
                "genre": "Pop Rock",
                "file": "worldismine.mp3",
                "cover": "worldismine.png"
            },
            {
                "title": "Senbonzakura",
                "creator": "Kurousa-P (WhiteFlame)",
                "genre": "Neo-Japanese Rock",
                "file": "senbonzakura.mp3",
                "cover": "senbonzakura.png"
            },
            {
                "title": "Rolling Girl",
                "creator": "wowaka",
                "genre": "Alt Rock",
                "file": "rollinggirl.mp3",
                "cover": "rollinggirl.png"
            },
            {
                "title": "ODDS&ENDS",
                "creator": "ryo (supercell)",
                "genre": "Ballad / Electronic Rock",
                "file": "oddsends.mp3",
                "cover": "oddsends.png"
            },
            {
                "title": "Ghost Rule",
                "creator": "DECO*27",
                "genre": "Hard Pop / Electro Rock",
                "file": "ghostrule.mp3",
                "cover": "ghostrule.png"
            },
            {
                "title": "Two-Faced Lovers",
                "creator": "wowaka",
                "genre": "Alt Rock / High BPM",
                "file": "twofacedlovers.mp3",
                "cover": "twofacedlovers.png"
            },
            {
                "title": "Unhappy Refrain",
                "creator": "wowaka",
                "genre": "Experimental Rock",
                "file": "unhappyrefrain.mp3",
                "cover": "unhappyrefrain.png"
            },
            {
                "title": "Sand Planet",
                "creator": "Hachi (Kenshi Yonezu)",
                "genre": "Indie Rock / Synthpop",
                "file": "sandplanet.mp3",
                "cover": "sandplanet.png"
            },
            {
                "title": "Streaming Heart",
                "creator": "DECO*27",
                "genre": "Electropop / Rock",
                "file": "streamingheart.mp3",
                "cover": "streamingheart.png"
            },
            {
                "title": "AI Kotoba II",
                "creator": "DECO*27",
                "genre": "Ballad / Synthpop",
                "file": "aikotobaii.mp3",
                "cover": "aikotobaii.png"
            },
            {
                "title": "Love Me, Love Me, Love Me",
                "creator": "DECO*27",
                "genre": "Dark Pop / Electro",
                "file": "lovemelovemeloveme.mp3",
                "cover": "lovemelovemeloveme.png"
            },
            {
                "title": "Night Sky Patrol of Tomorrow",
                "creator": "DECO*27",
                "genre": "Pop Rock / Dreamy",
                "file": "nightskypatroloftomorrow.mp3",
                "cover": "nightskypatroloftomorrow.png"
            }
        ]
        
        # Player state
        self.current_song_index = 0
        self.is_playing = False
        self.is_shuffle = False
        self.is_loop = False
        self.position = 0
        self.duration = 0
        self.shuffle_playlist = list(range(len(self.miku_bangers)))
        
        # GStreamer pipeline
        self.player = Gst.ElementFactory.make("playbin", "player")
        self.bus = self.player.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message", self.on_bus_message)
        
        # Set window properties
        self.set_default_size(960, 540)  # 16:9 aspect ratio
        self.set_resizable(True)
        
        # Create UI
        self.setup_ui()
        
        # Timer for position updates
        self.timer_id = GLib.timeout_add(1000, self.update_position)
        
        # Load first song info
        self.load_song_info()
        
    def setup_ui(self):
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        
        # Song info area
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        info_box.set_halign(Gtk.Align.CENTER)
        
        self.title_label = Gtk.Label()
        self.title_label.set_markup("<span size='x-large' weight='bold'>Select a song</span>")
        self.title_label.set_halign(Gtk.Align.CENTER)
        
        self.creator_label = Gtk.Label()
        self.creator_label.set_markup("<span size='medium'>Artist</span>")
        self.creator_label.set_halign(Gtk.Align.CENTER)
        
        self.genre_label = Gtk.Label()
        self.genre_label.set_markup("<span size='small' style='italic'>Genre</span>")
        self.genre_label.set_halign(Gtk.Align.CENTER)
        
        info_box.append(self.title_label)
        info_box.append(self.creator_label)
        info_box.append(self.genre_label)
        
        # Progress bar
        self.progress_bar = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
        self.progress_bar.set_range(0, 100)
        self.progress_bar.set_value(0)
        self.progress_bar.set_hexpand(True)
        self.progress_bar.connect("value-changed", self.on_seek)
        
        # Time labels
        time_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        time_box.set_halign(Gtk.Align.FILL)
        
        self.current_time_label = Gtk.Label(label="0:00")
        self.total_time_label = Gtk.Label(label="0:00")
        self.total_time_label.set_halign(Gtk.Align.END)
        
        time_box.append(self.current_time_label)
        time_box.append(Gtk.Box())  # Spacer
        time_box.append(self.total_time_label)
        
        # Control buttons
        control_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        control_box.set_halign(Gtk.Align.CENTER)
        
        # Previous button
        self.prev_button = Gtk.Button(label="⏮")
        self.prev_button.connect("clicked", self.on_previous)
        
        # Backward button
        self.backward_button = Gtk.Button(label="⏪")
        self.backward_button.connect("clicked", self.on_backward)
        
        # Play/Pause button
        self.play_pause_button = Gtk.Button(label="▶")
        self.play_pause_button.connect("clicked", self.on_play_pause)
        
        # Forward button
        self.forward_button = Gtk.Button(label="⏩")
        self.forward_button.connect("clicked", self.on_forward)
        
        # Next button
        self.next_button = Gtk.Button(label="⏭")
        self.next_button.connect("clicked", self.on_next)
        
        control_box.append(self.prev_button)
        control_box.append(self.backward_button)
        control_box.append(self.play_pause_button)
        control_box.append(self.forward_button)
        control_box.append(self.next_button)
        
        # Toggle buttons
        toggle_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        toggle_box.set_halign(Gtk.Align.CENTER)
        
        self.shuffle_button = Gtk.ToggleButton(label="🔀")
        self.shuffle_button.connect("toggled", self.on_shuffle_toggle)
        
        self.loop_button = Gtk.ToggleButton(label="🔁")
        self.loop_button.connect("toggled", self.on_loop_toggle)
        
        toggle_box.append(self.shuffle_button)
        toggle_box.append(self.loop_button)
        
        # Playlist
        playlist_frame = Gtk.Frame(label="Playlist")
        playlist_frame.set_margin_top(10)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(200)
        
        self.playlist_box = Gtk.ListBox()
        self.playlist_box.connect("row-selected", self.on_playlist_selection)
        
        # Populate playlist
        for i, song in enumerate(self.miku_bangers):
            row = Gtk.ListBoxRow()
            row.song_index = i
            
            song_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            song_box.set_margin_top(5)
            song_box.set_margin_bottom(5)
            song_box.set_margin_start(10)
            song_box.set_margin_end(10)
            
            title_label = Gtk.Label()
            title_label.set_markup(f"<span weight='bold'>{song['title']}</span>")
            title_label.set_halign(Gtk.Align.START)
            
            creator_label = Gtk.Label(label=f"by {song['creator']}")
            creator_label.set_halign(Gtk.Align.START)
            
            genre_label = Gtk.Label()
            genre_label.set_markup(f"<span size='small' style='italic'>{song['genre']}</span>")
            genre_label.set_halign(Gtk.Align.START)
            
            song_box.append(title_label)
            song_box.append(creator_label)
            song_box.append(genre_label)
            
            row.set_child(song_box)
            self.playlist_box.append(row)
        
        scrolled.set_child(self.playlist_box)
        playlist_frame.set_child(scrolled)
        
        # Pack everything
        main_box.append(info_box)
        main_box.append(self.progress_bar)
        main_box.append(time_box)
        main_box.append(control_box)
        main_box.append(toggle_box)
        main_box.append(playlist_frame)
        
        self.set_child(main_box)
        
    def load_song_info(self):
        """Load current song information"""
        song = self.miku_bangers[self.current_song_index]
        
        self.title_label.set_markup(f"<span size='x-large' weight='bold'>{song['title']}</span>")
        self.creator_label.set_markup(f"<span size='medium'>by {song['creator']}</span>")
        self.genre_label.set_markup(f"<span size='small' style='italic'>{song['genre']}</span>")
        
        # Highlight current song in playlist
        for i, row in enumerate(self.playlist_box):
            if i == self.current_song_index:
                row.set_css_classes(["activatable"])
            else:
                row.set_css_classes([])
        
        # Set background image
        self.set_background_image(song['cover'])
        
    def set_background_image(self, cover_filename):
        """Set window background to song cover"""
        try:
            if os.path.exists(cover_filename):
                # Create CSS for background image
                css_provider = Gtk.CssProvider()
                css_data = f"""
                window {{
                    background-image: url('{cover_filename}');
                    background-size: cover;
                    background-position: center;
                    background-repeat: no-repeat;
                }}
                """
                css_provider.load_from_data(css_data.encode())
                
                # Apply CSS
                display = Gdk.Display.get_default()
                Gtk.StyleContext.add_provider_for_display(
                    display, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                )
            else:
                print(f"Cover image not found: {cover_filename}")
                
        except Exception as e:
            print(f"Error setting background image: {e}")
            
    def on_play_pause(self, button):
        """Handle play/pause button"""
        if self.is_playing:
            self.pause()
        else:
            self.play()
            
    def play(self):
        """Start playing current song"""
        song = self.miku_bangers[self.current_song_index]
        file_path = song['file']
        
        if os.path.exists(file_path):
            self.player.set_property("uri", f"file://{os.path.abspath(file_path)}")
            self.player.set_state(Gst.State.PLAYING)
            self.is_playing = True
            self.play_pause_button.set_label("⏸")
        else:
            print(f"Audio file not found: {file_path}")
            
    def pause(self):
        """Pause playback"""
        self.player.set_state(Gst.State.PAUSED)
        self.is_playing = False
        self.play_pause_button.set_label("▶")
        
    def stop(self):
        """Stop playback"""
        self.player.set_state(Gst.State.NULL)
        self.is_playing = False
        self.play_pause_button.set_label("▶")
        self.position = 0
        self.progress_bar.set_value(0)
        
    def on_next(self, button):
        """Go to next song"""
        if self.is_shuffle:
            # Remove current song from shuffle list and pick random
            available = [i for i in self.shuffle_playlist if i != self.current_song_index]
            if available:
                self.current_song_index = random.choice(available)
            else:
                # Reshuffle if we've played all songs
                self.shuffle_playlist = list(range(len(self.miku_bangers)))
                self.current_song_index = random.choice(self.shuffle_playlist)
        else:
            self.current_song_index = (self.current_song_index + 1) % len(self.miku_bangers)
            
        self.load_song_info()
        if self.is_playing:
            self.stop()
            self.play()
            
    def on_previous(self, button):
        """Go to previous song"""
        if self.is_shuffle:
            # For shuffle, just pick a random song
            available = [i for i in range(len(self.miku_bangers)) if i != self.current_song_index]
            if available:
                self.current_song_index = random.choice(available)
        else:
            self.current_song_index = (self.current_song_index - 1) % len(self.miku_bangers)
            
        self.load_song_info()
        if self.is_playing:
            self.stop()
            self.play()
            
    def on_forward(self, button):
        """Skip forward 10 seconds"""
        if self.duration > 0:
            new_position = min(self.position + 10, self.duration)
            self.seek_to_position(new_position)
            
    def on_backward(self, button):
        """Skip backward 10 seconds"""
        new_position = max(self.position - 10, 0)
        self.seek_to_position(new_position)
        
    def seek_to_position(self, position):
        """Seek to specific position in seconds"""
        if self.player.get_state(0)[1] != Gst.State.NULL:
            self.player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, position * Gst.SECOND)
            
    def on_seek(self, scale):
        """Handle progress bar seeking"""
        if self.duration > 0:
            position = (scale.get_value() / 100) * self.duration
            self.seek_to_position(position)
            
    def on_shuffle_toggle(self, button):
        """Toggle shuffle mode"""
        self.is_shuffle = button.get_active()
        if self.is_shuffle:
            random.shuffle(self.shuffle_playlist)
            
    def on_loop_toggle(self, button):
        """Toggle loop mode"""
        self.is_loop = button.get_active()
        
    def on_playlist_selection(self, listbox, row):
        """Handle playlist selection"""
        if row:
            was_playing = self.is_playing
            self.stop()
            self.current_song_index = row.song_index
            self.load_song_info()
            if was_playing:
                self.play()
                
    def on_bus_message(self, bus, message):
        """Handle GStreamer bus messages"""
        if message.type == Gst.MessageType.EOS:
            # End of stream - go to next song or loop
            if self.is_loop:
                self.stop()
                self.play()
            else:
                self.on_next(None)
        elif message.type == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print(f"GStreamer Error: {err}, {debug}")
            
    def update_position(self):
        """Update playback position"""
        if self.player.get_state(0)[1] == Gst.State.PLAYING:
            try:
                success, position = self.player.query_position(Gst.Format.TIME)
                if success:
                    self.position = position / Gst.SECOND
                    
                success, duration = self.player.query_duration(Gst.Format.TIME)
                if success:
                    self.duration = duration / Gst.SECOND
                    
                    # Update progress bar
                    if self.duration > 0:
                        progress = (self.position / self.duration) * 100
                        self.progress_bar.set_value(progress)
                        
                    # Update time labels
                    self.current_time_label.set_text(self.format_time(self.position))
                    self.total_time_label.set_text(self.format_time(self.duration))
                    
            except Exception as e:
                print(f"Error updating position: {e}")
                
        return True  # Continue timer
        
    def format_time(self, seconds):
        """Format time in mm:ss format"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"
        
    def on_destroy(self, widget):
        """Cleanup on window close"""
        if self.timer_id:
            GLib.source_remove(self.timer_id)
        self.player.set_state(Gst.State.NULL)


class MikuTunesApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.example.mikutunes")
        
    def do_activate(self):
        window = MikuTunesPlayer(self)
        window.present()


if __name__ == "__main__":
    app = MikuTunesApp()
    app.run(sys.argv)
