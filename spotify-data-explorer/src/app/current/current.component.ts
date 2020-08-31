import { Component, OnInit } from '@angular/core';
import { AngularFirestore, AngularFirestoreDocument } from '@angular/fire/firestore';
import { Observable } from 'rxjs';
import { first } from 'rxjs/operators';
import { } from 'querystring';

export interface Item { name: string; }

const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
const WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

@Component({
  selector: 'app-current',
  templateUrl: './current.component.html',
  styleUrls: ['./current.component.css']
})
export class CurrentComponent implements OnInit {

    afs: AngularFirestore;

    private current_doc: AngularFirestoreDocument<Item>;
    current_item: Observable<Item>;

    constructor(afs: AngularFirestore) { 
        this.afs = afs;
        this.current_doc = afs.doc<Item>('overview/current');
        this.current_item = this.current_doc.valueChanges();
    }

    current_song = "";
    current_artist = "";
    current_album_img = "";

    artist_listens = 0;
    artist_time = "";
    artist_first = "";
    artist_last = "";

    track_listens = 0;
    track_time = "";
    track_first = "";
    track_last = "";

    ngOnInit() {
        this.current_item.subscribe(val => this.update_current(val))
    }

    transform_time(listen_time) {
        listen_time = listen_time/60000
        var listen_unit = "minutes"
        if(listen_time > 60) {
            listen_time = listen_time/60
            listen_unit = "hours"
            if(listen_time > 24) {
                listen_time = listen_time/24
                listen_unit = "days"
            }
        }
        return [listen_time.toFixed(2), listen_unit]
    }

    transform_date(date) {
        let day = date["day"]
        let month = MONTHS[date["month"]-1]
        let year = date["year"]
        return month + " " + day + ", " + year
    }

    populate_artist(val) {
        if(val === undefined) {
            this.artist_listens = 0
            this.artist_time = "0 minutes"
            this.artist_first = "This is your first time listening!"
            this.artist_last = ""
        }
        else {
            this.artist_listens = val["listen_count"]
            let time_info = this.transform_time(val["listen_time"])
            this.artist_time = time_info[0] + " " + time_info[1]
            this.artist_first = "First listened to on " + this.transform_date(val["first_listen_time"])
            this.artist_last = "Last listened to on " + this.transform_date(val["last_listen_time"])
        }
    }

    populate_song(val) {
        if(val === undefined) {
            this.track_listens = 0
            this.track_time = "0 minutes"
            this.track_first = "This is your first time listening!"
            this.track_last = ""
        }
        else {
            this.track_listens = val["listen_count"]
            let time_info = this.transform_time(val["listen_time"])
            this.track_time = time_info[0] + " " + time_info[1]
            this.track_first = "First listened to on " + this.transform_date(val["first_listen"])
            this.track_last = "Last listened to on " + this.transform_date(val["last_listen"])
        }
    }

    update_current(val) {
        this.current_song = val["song_name"];
        this.current_artist = val["artist_name"];
        this.current_album_img = val["album_img"];
        
        let artist_id = val["artist_id"]
        let track_id = val["track_id"]
        
        let artist_item = this.afs.doc<Item>('artists/' + artist_id).valueChanges()
        artist_item.pipe(first()).subscribe(val => this.populate_artist(val))

        let track_item = this.afs.doc<Item>('songs/' + track_id).valueChanges()
        track_item.pipe(first()).subscribe(val => this.populate_song(val))
    }

}
