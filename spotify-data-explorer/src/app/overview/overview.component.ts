import { Component, OnInit } from '@angular/core';
import { AngularFirestore, AngularFirestoreDocument } from '@angular/fire/firestore';
import { Observable } from 'rxjs';

import * as OVERVIEW_DATA from '../../assets/overview.json';

export interface Item { name: string; }

@Component({
    selector: 'app-overview',
    templateUrl: './overview.component.html',
    styleUrls: ['./overview.component.css']
})
export class OverviewComponent implements OnInit {
    private itemDoc: AngularFirestoreDocument<Item>;
    item: Observable<Item>;
    constructor(afs: AngularFirestore) { 
        this.itemDoc = afs.doc<Item>('overview/current');
        this.item = this.itemDoc.valueChanges();
    }

    current_song = "";
    current_artist = "";
    current_album_img = "";

    total_tracks;
    unique_tracks;
    unique_artists;
    time_hours;
    time_days;

    ngOnInit() {
        this.item.subscribe(val => this.update_current(val))
        let overview_data = (OVERVIEW_DATA as any).default;
        this.total_tracks = overview_data['total_tracks'];
        this.unique_tracks = overview_data['unique_tracks'];
        this.unique_artists = overview_data['unique_artists'];
        let time_ms = overview_data['total_ms'];
        let time_min = time_ms/1000/60;
        let time_hours = time_min/60;
        this.time_hours = (Math.round(100 * time_min/60) / 100).toFixed(2);
        this.time_days = (Math.round(100 * time_hours/24) / 100).toFixed(2);
    }

    update_current(val) {
        this.current_song = val["song_name"];
        this.current_artist = val["artist_name"];
        this.current_album_img = val["album_img"];
        console.log(this.current_album_img)
    }

}
