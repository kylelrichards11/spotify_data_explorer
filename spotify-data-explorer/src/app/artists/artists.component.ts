import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Params } from '@angular/router';
import { AngularFirestore, AngularFirestoreDocument } from '@angular/fire/firestore';
import { FormControl } from '@angular/forms';
import { Router } from '@angular/router';
import { Observable } from 'rxjs';
import { map, startWith } from 'rxjs/operators';
import { Chart } from 'chart.js';

const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

export interface Item { name: string; }

export interface SongListItem {
    track_id: string;
    song_name: string;
}

@Component({
    selector: 'app-artists',
    templateUrl: './artists.component.html',
    styleUrls: ['./artists.component.css']
})
export class ArtistsComponent implements OnInit {

    afs: AngularFirestore;

    /* INFO VARIABLES */
    artist_id: string;
    artist_name: string;
    artist_doc;
    artist_item;
    listen_count;
    listen_time;
    listen_time_unit;
    first_song_name;
    first_song_date;
    last_song_name;
    last_song_date;

    /* SONG LIST VARIABLES */
    song_control = new FormControl();
    song_options: SongListItem[];
    song_filtered_options: Observable<SongListItem[]>;
    selected_song;

    /* GRAPH VARIABLES */
    graph;
    tracks = {};
    active_dataset_time = "year";
    active_dataset_stat = "counts";
    active_time_unit;
    datasets = {
        "year" : {
            "counts": [],
            "times": []
        },
        "month" : {
            "counts": [],
            "times": []
        }
    }

    labels = {
        "year": ["2015", "2016", "2017", "2018", "2019", "2020"],
        "month": ['1/2015', '2/2015', '3/2015', '4/2015', '5/2015', '6/2015', '7/2015', '8/2015', '9/2015', '10/2015', '11/2015', '12/2015', '1/2016', '2/2016', '3/2016', '4/2016', '5/2016', '6/2016', '7/2016', '8/2016', '9/2016', '10/2016', '11/2016', '12/2016', '1/2017', '2/2017', '3/2017', '4/2017', '5/2017', '6/2017', '7/2017', '8/2017', '9/2017', '10/2017', '11/2017', '12/2017', '1/2018', '2/2018', '3/2018', '4/2018', '5/2018', '6/2018', '7/2018', '8/2018', '9/2018', '10/2018', '11/2018', '12/2018', '1/2019', '2/2019', '3/2019', '4/2019', '5/2019', '6/2019', '7/2019', '8/2019', '9/2019', '10/2019', '11/2019', '12/2019', '1/2020', '2/2020', '3/2020', '4/2020', '5/2020', '6/2020', '7/2020', '8/2020', '9/2020', '10/2020', '11/2020', '12/2020']
    }

    titles = {
        "times" : {
            "year": " Listened per Year",
            "month": " Listened per Month"
        },
        "counts" : {
            "year": "Listens per Year",
            "month": "Listens per Month"
        }
    }

    xlabels = {
        "year": "Year",
        "month": "Month"
    }

    constructor(private activated_route: ActivatedRoute, private router: Router, afs: AngularFirestore) {
        this.afs = afs;
    }

    ngOnInit() {
        this.activated_route.params.subscribe((params: Params) => {
            this.artist_id = params["id"]
        })

        // Subscribe to artist
        this.artist_doc = this.afs.doc<Item>('artists/' + this.artist_id);
        this.artist_item = this.artist_doc.valueChanges();
        this.artist_item.subscribe(val => this.populate_info(val))

        let canvas = <HTMLCanvasElement>document.getElementById('canvas');
        let context = canvas.getContext('2d');
        this.graph = new Chart(context, {
            "type": "bar",
            "data": {
                "datasets": [{
                    data: [0, 0, 0, 0, 0, 0],
                    backgroundColor: '#08a1d4'
                }],
                "labels": this.labels["year"]
            },
            "options": {
                maintainAspectRatio: false,
                responsive: true,
                scales : {
                    xAxes: [{
                        ticks: {
                            fontColor: "black"
                        },
                        scaleLabel: {
                            display: true,
                            labelString: "Year",
                            fontColor: "black",
                            fontSize: 16
                        }
                    }],
                    yAxes: [{
                        ticks: {
                            beginAtZero: true,
                            fontColor: "black"
                        },
                        scaleLabel: {
                            display: true,
                            labelString: "Listens",
                            fontColor: "black",
                            fontSize: 16
                        }
                    }]
                },
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: "Listens per Year",
                    fontSize: 18,
                    fontFamily: "Arial",
                    fontColor: "black",
                },
            }
        });
    }

    /* SONG LIST FUNCTIONS */
    update_song_options(val) {
        this.song_options = val["tracks"].sort((a, b) => (a.song_name > b.song_name) ? 1 : -1)
        this.song_filtered_options = this.song_control.valueChanges
            .pipe(
                startWith(''),
                map(value => typeof value === 'string' ? value : value.name),
                map(name => name ? this._filter_song(name) : this.song_options.slice())
            );
    }

    song_display_fn(song: SongListItem): string {
        return song && song.song_name ? song.song_name : '';
    }

    private _filter_song(value: string): SongListItem[] {
        const filterValue = value.toLowerCase();
        return this.song_options.filter(option =>
            option.song_name.toLowerCase().includes(filterValue) ||
            option.song_name.toLowerCase().replace(/ [a-z]\./, "").includes(filterValue) ||
            option.song_name.toLowerCase().replace(/\./g, "").includes(filterValue)
        );
    }

    select_song(option) {
        this.selected_song = option;
    }

    submit_song() {
        this.router.navigateByUrl('/song/' + this.selected_song.track_id)
    }

    /* INFO AND GRAPH FUNCTIONS */

    populate_info(val) {
        this.artist_name = val["artist_name"]
        this.listen_count = val["listen_count"]
        let time_info = this.transform_time(val["listen_time"]);
        this.listen_time = time_info[0]
        this.listen_time_unit = time_info[1]
        this.first_song_name = val["first_listen"]["song_name"]
        let flt = val["first_listen_time"]
        this.first_song_date = MONTHS[flt["month"] - 1] + " " + flt["day"] + ", " + flt["year"]

        this.last_song_name = val["last_listen"]["song_name"]
        let llt = val["last_listen_time"]
        this.last_song_date = MONTHS[llt["month"] - 1] + " " + llt["day"] + ", " + llt["year"]
        this.set_chart_data(val["tracks"])
        this.update_song_options(val);
    }

    set_chart_data(tracks) {
        tracks.forEach(track => {
            let track_doc = this.afs.doc<Item>('songs/' + track["track_id"]);
            let track_item = track_doc.valueChanges();
            track_item.subscribe(val => this.update_track(val))
        });
    }

    update_track(track) {
        this.tracks[track["track_id"]] = {}
        this.tracks[track["track_id"]]["listens"] = track["listens"]
        this.recount_stats()
    }

    recount_stats() {
        var year_counts = { 2015: 0, 2016: 0, 2017: 0, 2018: 0, 2019: 0, 2020: 0 };
        var year_times = { 2015: 0, 2016: 0, 2017: 0, 2018: 0, 2019: 0, 2020: 0 };
        var month_counts = {'1/2015': 0, '2/2015': 0, '3/2015': 0, '4/2015': 0, '5/2015': 0, '6/2015': 0, '7/2015': 0, '8/2015': 0, '9/2015': 0, '10/2015': 0, '11/2015': 0, '12/2015': 0, '1/2016': 0, '2/2016': 0, '3/2016': 0, '4/2016': 0, '5/2016': 0, '6/2016': 0, '7/2016': 0, '8/2016': 0, '9/2016': 0, '10/2016': 0, '11/2016': 0, '12/2016': 0, '1/2017': 0, '2/2017': 0, '3/2017': 0, '4/2017': 0, '5/2017': 0, '6/2017': 0, '7/2017': 0, '8/2017': 0, '9/2017': 0, '10/2017': 0, '11/2017': 0, '12/2017': 0, '1/2018': 0, '2/2018': 0, '3/2018': 0, '4/2018': 0, '5/2018': 0, '6/2018': 0, '7/2018': 0, '8/2018': 0, '9/2018': 0, '10/2018': 0, '11/2018': 0, '12/2018': 0, '1/2019': 0, '2/2019': 0, '3/2019': 0, '4/2019': 0, '5/2019': 0, '6/2019': 0, '7/2019': 0, '8/2019': 0, '9/2019': 0, '10/2019': 0, '11/2019': 0, '12/2019': 0, '1/2020': 0, '2/2020': 0, '3/2020': 0, '4/2020': 0, '5/2020': 0, '6/2020': 0, '7/2020': 0, '8/2020': 0, '9/2020': 0, '10/2020': 0, '11/2020': 0, '12/2020': 0};
        var month_times = {'1/2015': 0, '2/2015': 0, '3/2015': 0, '4/2015': 0, '5/2015': 0, '6/2015': 0, '7/2015': 0, '8/2015': 0, '9/2015': 0, '10/2015': 0, '11/2015': 0, '12/2015': 0, '1/2016': 0, '2/2016': 0, '3/2016': 0, '4/2016': 0, '5/2016': 0, '6/2016': 0, '7/2016': 0, '8/2016': 0, '9/2016': 0, '10/2016': 0, '11/2016': 0, '12/2016': 0, '1/2017': 0, '2/2017': 0, '3/2017': 0, '4/2017': 0, '5/2017': 0, '6/2017': 0, '7/2017': 0, '8/2017': 0, '9/2017': 0, '10/2017': 0, '11/2017': 0, '12/2017': 0, '1/2018': 0, '2/2018': 0, '3/2018': 0, '4/2018': 0, '5/2018': 0, '6/2018': 0, '7/2018': 0, '8/2018': 0, '9/2018': 0, '10/2018': 0, '11/2018': 0, '12/2018': 0, '1/2019': 0, '2/2019': 0, '3/2019': 0, '4/2019': 0, '5/2019': 0, '6/2019': 0, '7/2019': 0, '8/2019': 0, '9/2019': 0, '10/2019': 0, '11/2019': 0, '12/2019': 0, '1/2020': 0, '2/2020': 0, '3/2020': 0, '4/2020': 0, '5/2020': 0, '6/2020': 0, '7/2020': 0, '8/2020': 0, '9/2020': 0, '10/2020': 0, '11/2020': 0, '12/2020': 0};
        for (let track_id in this.tracks) {
            for (let listen_idx in this.tracks[track_id]["listens"]) {
                let listen_year = this.tracks[track_id]["listens"][listen_idx]["year"]
                let listen_month = this.tracks[track_id]["listens"][listen_idx]["month"] + "/" + listen_year;
                let ms_played = this.tracks[track_id]["listens"][listen_idx]["duration"]
                year_counts[listen_year] += 1;
                year_times[listen_year] += ms_played
                month_counts[listen_month] += 1;
                month_times[listen_month] += ms_played;
            }
        }
        // YEARS
        var year_count_data = []
        var year_time_data = []

        var max_year_time = -1;
        var max_year;
        for (let year in year_times) {
            let year_time = year_times[year]
            if(year_time > max_year_time) {
                max_year_time = year_time;
                max_year = year;
            }
        }
        let year_unit = this.transform_time(max_year_time)[1];
        if(this.active_dataset_time == "year") {
            this.active_time_unit = year_unit;
        }

        for (let year in year_counts) {
            year_count_data.push(year_counts[year])    
        }
        for (let year in year_times) {
            year_time_data.push(this.transform_time_unit(year_times[year], year_unit))
        }

        this.datasets["year"]["counts"] = year_count_data;
        this.datasets["year"]["times"] = year_time_data;

        // MONTHS
        var month_count_data = []
        var month_time_data = []

        var max_month_time = -1;
        var max_month;
        for (let month in month_times) {
            let month_time = month_times[month]
            if(month_time > max_month_time) {
                max_month_time = month_time;
                max_month = month;
            }
        }
        let month_unit = this.transform_time(max_month_time)[1];
        if(this.active_dataset_time == "month") {
            this.active_time_unit = month_unit;
        }

        for (let month in month_counts) {
            month_count_data.push(month_counts[month])    
        }
        for (let month in month_times) {
            month_time_data.push(this.transform_time_unit(month_times[month], month_unit))
        }

        this.datasets["month"]["counts"] = month_count_data;
        this.datasets["month"]["times"] = month_time_data;

        this.graph["data"]["datasets"][0]["data"] = this.datasets[this.active_dataset_time][this.active_dataset_stat]
        this.graph.update()
    }

    transform_time(listen_time) {
        listen_time = listen_time / 60000
        var listen_unit = "Minutes"
        if (listen_time > 60) {
            listen_time = listen_time / 60
            listen_unit = "Hours"
            if (listen_time > 24) {
                listen_time = listen_time / 24
                listen_unit = "Days"
            }
        }
        return [listen_time.toFixed(2), listen_unit]
    }

    transform_time_unit(listen_time, unit) {
        listen_time = listen_time / 60000
        if (unit == "Hours") {
            listen_time = listen_time / 60
            if (unit == "Days") {
                listen_time = listen_time / 24
            }
        }
        return listen_time.toFixed(2)
    }

    change_timescale(timescale) {
        this.active_dataset_time = timescale;
        this.graph["data"]["labels"] = this.labels[timescale]
        this.graph["data"]["datasets"][0]["data"] = this.datasets[timescale][this.active_dataset_stat]
        this.graph["options"]["scales"]["xAxes"][0]["scaleLabel"]["labelString"] = this.xlabels[timescale]
        if(this.active_dataset_stat == "times") {
            this.graph["options"]["title"]["text"] = this.active_time_unit + this.titles[this.active_dataset_stat][timescale]
        }
        else {
            this.graph["options"]["title"]["text"] = this.titles[this.active_dataset_stat][timescale]
        }
        this.graph.update()
    }

    change_stat(stat) {
        this.active_dataset_stat = stat;
        this.graph["data"]["datasets"][0]["data"] = this.datasets[this.active_dataset_time][stat]
        if(stat == "times") {
            this.graph["options"]["scales"]["yAxes"][0]["scaleLabel"]["labelString"] = this.active_time_unit
        }
        else {
            this.graph["options"]["scales"]["yAxes"][0]["scaleLabel"]["labelString"] = "Listens"
        }
        if(stat == "times") {
            this.graph["options"]["title"]["text"] = this.active_time_unit + this.titles[stat][this.active_dataset_time]
        }
        else {
            this.graph["options"]["title"]["text"] = this.titles[stat][this.active_dataset_time]
        }
        this.graph.update()
    }
}
