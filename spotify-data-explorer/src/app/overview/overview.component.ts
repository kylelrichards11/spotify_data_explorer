import { Component, OnInit } from '@angular/core';
import { AngularFirestore, AngularFirestoreDocument } from '@angular/fire/firestore';
import { Observable } from 'rxjs';

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

    ngOnInit() {
        this.item.subscribe(val => this.update_current(val))
    }

    update_current(val) {
        this.current_song = val["song_name"];
        this.current_artist = val["artist_name"];
        this.current_album_img = val["album_img"];
        console.log(this.current_album_img)
    }

}
