import { Component, OnInit } from '@angular/core';
import { FormControl } from '@angular/forms';
import { Router } from '@angular/router';
import { Observable } from 'rxjs';
import { map, startWith } from 'rxjs/operators';
import { AngularFirestore, AngularFirestoreDocument } from '@angular/fire/firestore';

export interface Item { name: string; }

export interface ArtistListItem {
    artist_id: string;
    artist_name: string;
}

@Component({
    selector: 'app-search',
    templateUrl: './search.component.html',
    styleUrls: ['./search.component.css']
})
export class SearchComponent implements OnInit {
    artist_control = new FormControl();
    artist_options: ArtistListItem[];
    artist_filtered_options: Observable<ArtistListItem[]>;
    private artist_list_doc: AngularFirestoreDocument<Item>;

    artist_item: Observable<Item>;
    selected_artist;

    constructor(private router: Router, afs: AngularFirestore) {
        this.artist_list_doc = afs.doc<Item>('utils/artist_list');
        this.artist_item = this.artist_list_doc.valueChanges();
    }

    ngOnInit() {
        this.artist_item.subscribe(val => this.update_artist_options(val))
    }

    update_artist_options(val) {
        this.artist_options = val.list.sort((a, b) => (a.artist_name > b.artist_name) ? 1 : -1)
        this.artist_filtered_options = this.artist_control.valueChanges
            .pipe(
                startWith(''),
                map(value => typeof value === 'string' ? value : value.name),
                map(name => name ? this._filter_artist(name) : this.artist_options.slice())
            );
    }

    artist_display_fn(artist: ArtistListItem): string {
        return artist && artist.artist_name ? artist.artist_name : '';
    }

    private _filter_artist(value: string): ArtistListItem[] {
        const filterValue = value.toLowerCase();
        return this.artist_options.filter(option =>
            option.artist_name.toLowerCase().includes(filterValue) ||
            option.artist_name.toLowerCase().replace(/ [a-z]\./, "").includes(filterValue) ||
            option.artist_name.toLowerCase().replace(/\./g, "").includes(filterValue)
        );
    }

    select_artist(option){
        this.selected_artist = option;
    }

    submit_artist() {
        this.router.navigateByUrl('/artist/'+this.selected_artist.artist_id)
    }

}
