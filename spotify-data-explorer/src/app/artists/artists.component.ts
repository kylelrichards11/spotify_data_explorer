import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Params } from '@angular/router';
import { AngularFirestore, AngularFirestoreDocument } from '@angular/fire/firestore';
import { FormControl } from '@angular/forms';
import { Router } from '@angular/router';
import { Observable } from 'rxjs';
import { map, startWith } from 'rxjs/operators';
import { Chart } from 'chart.js';

const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
const MONTH_KEYS = ['10/2015', '11/2015', '12/2015', '1/2016', '2/2016', '3/2016', '4/2016', '5/2016', '6/2016', '7/2016', '8/2016', '9/2016', '10/2016', '11/2016', '12/2016', '1/2017', '2/2017', '3/2017', '4/2017', '5/2017', '6/2017', '7/2017', '8/2017', '9/2017', '10/2017', '11/2017', '12/2017', '1/2018', '2/2018', '3/2018', '4/2018', '5/2018', '6/2018', '7/2018', '8/2018', '9/2018', '10/2018', '11/2018', '12/2018', '1/2019', '2/2019', '3/2019', '4/2019', '5/2019', '6/2019', '7/2019', '8/2019', '9/2019', '10/2019', '11/2019', '12/2019', '1/2020', '2/2020', '3/2020', '4/2020', '5/2020', '6/2020', '7/2020', '8/2020', '9/2020', '10/2020', '11/2020', '12/2020', '1/2021', '2/2021', '3/2021', '4/2021', '5/2021', '6/2021', '7/2021', '8/2021', '9/2021', '10/2021', '11/2021', '12/2021', '1/2022', '2/2022', '3/2022', '4/2022', '5/2022', '6/2022', '7/2022', '8/2022', '9/2022', '10/2022', '11/2022', '12/2022']
const YEAR_KEYS = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022]

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
    artist_listen_count;
    artist_listen_time;
    artist_listen_time_unit;
    unique_songs;
    artist_first_song_name;
    artist_first_song_date;
    artist_last_song_name;
    artist_last_song_date;
    most_pc_song;
    most_pc;
    most_time_song;
    most_time;
    song_listen_count;
    song_listen_time;
    song_listen_time_unit;
    song_first_song_date;
    song_last_song_date;

    /* SONG LIST VARIABLES */
    song_control = new FormControl();
    song_options: SongListItem[];
    song_filtered_options: Observable<SongListItem[]>;

    /* GRAPH VARIABLES */
    artist_graph;
    song_graph;
    tracks = {};
    active_artist_dataset_time = "month";
    active_artist_dataset_stat = "counts";
    active_artist_time_unit = {
        "month": "",
        "year": ""
    }
    artist_datasets = {
        "year": {
            "counts": [],
            "times": [],
            "uq_songs": []
        },
        "month": {
            "counts": [],
            "times": [],
            "uq_songs": []
        }
    }

    active_song_dataset_time = "month";
    active_song_dataset_stat = "counts";
    active_song_time_unit = {
        "month": "",
        "year": ""
    }
    song_datasets = {
        "year": {
            "counts": [],
            "times": [],
            "uq_songs": []
        },
        "month": {
            "counts": [],
            "times": [],
            "uq_songs": []
        }
    }

    labels = {
        "year": YEAR_KEYS,
        "month": MONTH_KEYS
    }

    titles = {
        "times": {
            "year": " Listened per Year",
            "month": " Listened per Month"
        },
        "counts": {
            "year": "Listens per Year",
            "month": "Listens per Month"
        },
        "uq_songs": {
            "year": "Unique Songs per Year",
            "month": "Unique Songs per Month"
        }
    }

    xlabels = {
        "year": "Year",
        "month": "Month"
    }

    ylabels = {
        "counts": "Listens",
        "uq_songs": "Unique Songs"
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

        // Define artist graph
        let artist_canvas = <HTMLCanvasElement>document.getElementById('artist_canvas');
        let artist_context = artist_canvas.getContext('2d');
        this.artist_graph = new Chart(artist_context, {
            "type": "bar",
            "data": {
                "datasets": [{
                    data: [0, 0, 0, 0, 0, 0, 0, 0],
                    backgroundColor: '#08a1d4'
                }],
                "labels": this.labels["month"]
            },
            "options": {
                maintainAspectRatio: false,
                responsive: true,
                scales: {
                    xAxes: [{
                        ticks: {
                            fontColor: "black"
                        },
                        scaleLabel: {
                            display: true,
                            labelString: "Month",
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
                    text: "Listens per Month",
                    fontSize: 18,
                    fontFamily: "Arial",
                    fontColor: "black",
                },
            }
        });

        // Define song graph
        let song_canvas = <HTMLCanvasElement>document.getElementById('song_canvas');
        let song_context = song_canvas.getContext('2d');
        this.song_graph = new Chart(song_context, {
            "type": "bar",
            "data": {
                "datasets": [{
                    data: [0, 0, 0, 0, 0, 0, 0, 0],
                    backgroundColor: '#08a1d4'
                }],
                "labels": this.labels["month"]
            },
            "options": {
                maintainAspectRatio: false,
                responsive: true,
                scales: {
                    xAxes: [{
                        ticks: {
                            fontColor: "black"
                        },
                        scaleLabel: {
                            display: true,
                            labelString: "Month",
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
                    text: "Listens per Month",
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

    select_song(event) {
        this.set_song_chart_data(this.tracks[event.option.value.track_id])
    }

    /* INFO AND GRAPH FUNCTIONS */
    populate_info(val) {
        this.artist_name = val["artist_name"]
        this.artist_listen_count = val["listen_count"]
        let time_info = this.transform_time(val["listen_time"]);
        this.artist_listen_time = time_info[0]
        this.artist_listen_time_unit = time_info[1].toLowerCase()
        this.unique_songs = val["tracks"].length;

        (<HTMLAnchorElement>document.getElementById("first_song_link")).href = '/song/' + val["first_listen"]["track_id"]
        this.artist_first_song_name = val["first_listen"]["song_name"]
        let flt = val["first_listen_time"]
        this.artist_first_song_date = MONTHS[flt["month"] - 1] + " " + flt["day"] + ", " + flt["year"];

        (<HTMLAnchorElement>document.getElementById("last_song_link")).href = '/song/' + val["last_listen"]["track_id"]
        this.artist_last_song_name = val["last_listen"]["song_name"]
        let llt = val["last_listen_time"]
        this.artist_last_song_date = MONTHS[llt["month"] - 1] + " " + llt["day"] + ", " + llt["year"]

        this.set_artist_chart_data(val["tracks"])
        this.update_song_options(val);
    }

    set_artist_chart_data(tracks) {
        tracks.forEach(track => {
            let track_doc = this.afs.doc<Item>('songs/' + track["track_id"]);
            let track_item = track_doc.valueChanges();
            track_item.subscribe(val => this.update_track(val))
        });
    }

    set_song_chart_data(track_info) {
        // Populate info
        this.song_listen_count = track_info["listen_count"]
        let song_time_info = this.transform_time(track_info["listen_time"])
        this.song_listen_time = song_time_info[0]
        this.song_listen_time_unit = song_time_info[1]
        let fl = track_info["first_listen"]
        let ll = track_info["last_listen"]
        this.song_first_song_date = MONTHS[fl["month"] - 1] + " " + fl["day"] + ", " + fl["year"];
        this.song_last_song_date = MONTHS[ll["month"] - 1] + " " + ll["day"] + ", " + ll["year"];

        var year_counts = this.init_dict("year", 0)
        var year_times = this.init_dict("year", 0)
        var month_counts = this.init_dict("month", 0)
        var month_times = this.init_dict("month", 0)
        for (let listen_idx in track_info["listens"]) {
            let listen_year = track_info["listens"][listen_idx]["year"]
            let listen_month = track_info["listens"][listen_idx]["month"] + "/" + listen_year;
            let ms_played = track_info["listens"][listen_idx]["duration"]
            year_counts[listen_year] += 1;
            year_times[listen_year] += ms_played
            month_counts[listen_month] += 1;
            month_times[listen_month] += ms_played;
        }

        // Calculate year values
        var year_count_data = []
        var year_time_data = []

        var max_year_time = -1;
        var max_year;
        for (let year in year_times) {
            let year_time = year_times[year]
            if (year_time > max_year_time) {
                max_year_time = year_time;
                max_year = year;
            }
        }
        let year_unit = this.transform_time(max_year_time)[1];
        this.active_song_time_unit["year"] = year_unit;

        for (let year in year_counts) {
            year_count_data.push(year_counts[year])
        }
        for (let year in year_times) {
            year_time_data.push(this.transform_time_unit(year_times[year], year_unit))
        }

        this.song_datasets["year"]["counts"] = year_count_data;
        this.song_datasets["year"]["times"] = year_time_data;

        // Calculate month values
        var month_count_data = []
        var month_time_data = []

        var max_month_time = -1;
        var max_month;
        for (let month in month_times) {
            let month_time = month_times[month]
            if (month_time > max_month_time) {
                max_month_time = month_time;
                max_month = month;
            }
        }
        let month_unit = this.transform_time(max_month_time)[1];
        this.active_song_time_unit["month"] = month_unit;

        for (let month in month_counts) {
            month_count_data.push(month_counts[month])
        }
        for (let month in month_times) {
            month_time_data.push(this.transform_time_unit(month_times[month], month_unit))
        }

        this.song_datasets["month"]["counts"] = month_count_data;
        this.song_datasets["month"]["times"] = month_time_data;

        this.song_graph["data"]["datasets"][0]["data"] = this.song_datasets[this.active_song_dataset_time][this.active_song_dataset_stat]
        this.song_graph.update()
    }

    update_track(track) {
        this.tracks[track["track_id"]] = track
        this.recount_stats()
    }

    init_dict(timescale, default_val) {
        let arr = (timescale == "year") ? YEAR_KEYS : MONTH_KEYS;
        var my_dict = {}
        arr.forEach(key => {
            if (default_val == "set") {
                my_dict[key] = new Set();
            }
            else {
                my_dict[key] = 0;
            }
        });
        return my_dict
    }

    recount_stats() {
        var year_counts = this.init_dict("year", 0)
        var year_times = this.init_dict("year", 0)
        var year_unique_songs = this.init_dict("year", "set")
        var month_counts = this.init_dict("month", 0)
        var month_times = this.init_dict("month", 0)
        var month_unique_songs = this.init_dict("month", "set")

        // Most played
        var highest_pc = 0;
        var highest_pc_song;
        var highest_time = 0;
        var highest_time_song;
        for (let track_id in this.tracks) {
            let pc = this.tracks[track_id]["listen_count"]
            let play_time = this.tracks[track_id]["listen_time"]
            let song_name = this.tracks[track_id]["song_name"]
            if (pc > highest_pc) {
                highest_pc = pc;
                highest_pc_song = song_name;
            }
            if (play_time > highest_time) {
                highest_time = play_time;
                highest_time_song = song_name
            }
        }
        this.most_pc_song = highest_pc_song
        this.most_pc = highest_pc
        this.most_time_song = highest_time_song
        let most_time_info = this.transform_time(highest_time)
        this.most_time = most_time_info[0] + " " + most_time_info[1]

        for (let track_id in this.tracks) {
            for (let listen_idx in this.tracks[track_id]["listens"]) {
                let listen_year = this.tracks[track_id]["listens"][listen_idx]["year"]
                let listen_month = this.tracks[track_id]["listens"][listen_idx]["month"] + "/" + listen_year;
                let ms_played = this.tracks[track_id]["listens"][listen_idx]["duration"]
                year_counts[listen_year] += 1;
                year_times[listen_year] += ms_played
                year_unique_songs[listen_year].add(track_id)
                month_counts[listen_month] += 1;
                month_times[listen_month] += ms_played;
                month_unique_songs[listen_month].add(track_id)
            }
        }
        // YEARS
        var year_count_data = []
        var year_time_data = []
        var year_unique_songs_data = []

        var max_year_time = -1;
        var max_year;
        for (let year in year_times) {
            let year_time = year_times[year]
            if (year_time > max_year_time) {
                max_year_time = year_time;
                max_year = year;
            }
        }
        let year_unit = this.transform_time(max_year_time)[1];
        this.active_artist_time_unit["year"] = year_unit;

        for (let year in year_counts) {
            year_count_data.push(year_counts[year])
        }
        for (let year in year_times) {
            year_time_data.push(this.transform_time_unit(year_times[year], year_unit))
        }
        for (let year in year_unique_songs) {
            year_unique_songs_data.push(year_unique_songs[year].size)
        }

        this.artist_datasets["year"]["counts"] = year_count_data;
        this.artist_datasets["year"]["times"] = year_time_data;
        this.artist_datasets["year"]["uq_songs"] = year_unique_songs_data;

        // MONTHS
        var month_count_data = []
        var month_time_data = []
        var month_unique_songs_data = []

        var max_month_time = -1;
        var max_month;
        for (let month in month_times) {
            let month_time = month_times[month]
            if (month_time > max_month_time) {
                max_month_time = month_time;
                max_month = month;
            }
        }
        let month_unit = this.transform_time(max_month_time)[1];
        this.active_artist_time_unit["month"] = month_unit;

        for (let month in month_counts) {
            month_count_data.push(month_counts[month])
        }
        for (let month in month_times) {
            month_time_data.push(this.transform_time_unit(month_times[month], month_unit))
        }
        for (let month in month_unique_songs) {
            month_unique_songs_data.push(month_unique_songs[month].size)
        }

        this.artist_datasets["month"]["counts"] = month_count_data;
        this.artist_datasets["month"]["times"] = month_time_data;
        this.artist_datasets["month"]["uq_songs"] = month_unique_songs_data;

        this.artist_graph["data"]["datasets"][0]["data"] = this.artist_datasets[this.active_artist_dataset_time][this.active_artist_dataset_stat]
        this.artist_graph.update()
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
        }
        else if (unit == "Days") {
            listen_time = listen_time / (60 * 24)
        }
        return listen_time.toFixed(2)
    }

    // Chart Button Functions
    change_artist_timescale(timescale) {
        this.active_artist_dataset_time = timescale;
        this.artist_graph["data"]["labels"] = this.labels[timescale]
        this.artist_graph["data"]["datasets"][0]["data"] = this.artist_datasets[timescale][this.active_artist_dataset_stat]
        this.artist_graph["options"]["scales"]["xAxes"][0]["scaleLabel"]["labelString"] = this.xlabels[timescale]
        if (this.active_artist_dataset_stat == "times") {
            this.artist_graph["options"]["title"]["text"] = this.active_artist_time_unit[timescale] + this.titles[this.active_artist_dataset_stat][timescale]
        }
        else {
            this.artist_graph["options"]["title"]["text"] = this.titles[this.active_artist_dataset_stat][timescale]
        }
        if (this.active_artist_dataset_stat == "times") {
            this.artist_graph["options"]["scales"]["yAxes"][0]["scaleLabel"]["labelString"] = this.active_artist_time_unit[timescale]
        }
        this.artist_graph.update()
    }

    change_artist_stat(stat) {
        this.active_artist_dataset_stat = stat;
        this.artist_graph["data"]["datasets"][0]["data"] = this.artist_datasets[this.active_artist_dataset_time][stat]
        if (stat == "times") {
            this.artist_graph["options"]["scales"]["yAxes"][0]["scaleLabel"]["labelString"] = this.active_artist_time_unit[this.active_artist_dataset_time]
        }
        else {
            this.artist_graph["options"]["scales"]["yAxes"][0]["scaleLabel"]["labelString"] = this.ylabels[stat]
        }
        if (stat == "times") {
            this.artist_graph["options"]["title"]["text"] = this.active_artist_time_unit[this.active_artist_dataset_time] + this.titles[stat][this.active_artist_dataset_time]
        }
        else {
            this.artist_graph["options"]["title"]["text"] = this.titles[stat][this.active_artist_dataset_time]
        }
        this.artist_graph.update()
    }

    change_song_timescale(timescale) {
        this.active_song_dataset_time = timescale;
        this.song_graph["data"]["labels"] = this.labels[timescale]
        this.song_graph["data"]["datasets"][0]["data"] = this.song_datasets[timescale][this.active_song_dataset_stat]
        this.song_graph["options"]["scales"]["xAxes"][0]["scaleLabel"]["labelString"] = this.xlabels[timescale]
        if (this.active_song_dataset_stat == "times") {
            this.song_graph["options"]["title"]["text"] = this.active_song_time_unit[timescale] + this.titles[this.active_song_dataset_stat][timescale]
        }
        else {
            this.song_graph["options"]["title"]["text"] = this.titles[this.active_song_dataset_stat][timescale]
        }
        if (this.active_song_dataset_stat == "times") {
            this.song_graph["options"]["scales"]["yAxes"][0]["scaleLabel"]["labelString"] = this.active_song_time_unit[timescale]
        }
        this.song_graph.update()
    }

    change_song_stat(stat) {
        this.active_song_dataset_stat = stat;
        this.song_graph["data"]["datasets"][0]["data"] = this.song_datasets[this.active_song_dataset_time][stat]
        if (stat == "times") {
            this.song_graph["options"]["scales"]["yAxes"][0]["scaleLabel"]["labelString"] = this.active_song_time_unit[this.active_song_dataset_time]
        }
        else {
            this.song_graph["options"]["scales"]["yAxes"][0]["scaleLabel"]["labelString"] = "Listens"
        }
        if (stat == "times") {
            this.song_graph["options"]["title"]["text"] = this.active_song_time_unit[this.active_song_dataset_time] + this.titles[stat][this.active_song_dataset_time]
        }
        else {
            this.song_graph["options"]["title"]["text"] = this.titles[stat][this.active_song_dataset_time]
        }
        this.song_graph.update()
    }
}
