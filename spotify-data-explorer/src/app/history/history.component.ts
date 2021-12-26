import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Params } from '@angular/router';
import { AngularFirestore } from '@angular/fire/firestore';
import { Router } from '@angular/router';
import { Chart } from 'chart.js';

const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
const MONTH_EMPTY = { '10/2015': 0, '11/2015': 0, '12/2015': 0, '1/2016': 0, '2/2016': 0, '3/2016': 0, '4/2016': 0, '5/2016': 0, '6/2016': 0, '7/2016': 0, '8/2016': 0, '9/2016': 0, '10/2016': 0, '11/2016': 0, '12/2016': 0, '1/2017': 0, '2/2017': 0, '3/2017': 0, '4/2017': 0, '5/2017': 0, '6/2017': 0, '7/2017': 0, '8/2017': 0, '9/2017': 0, '10/2017': 0, '11/2017': 0, '12/2017': 0, '1/2018': 0, '2/2018': 0, '3/2018': 0, '4/2018': 0, '5/2018': 0, '6/2018': 0, '7/2018': 0, '8/2018': 0, '9/2018': 0, '10/2018': 0, '11/2018': 0, '12/2018': 0, '1/2019': 0, '2/2019': 0, '3/2019': 0, '4/2019': 0, '5/2019': 0, '6/2019': 0, '7/2019': 0, '8/2019': 0, '9/2019': 0, '10/2019': 0, '11/2019': 0, '12/2019': 0, '1/2020': 0, '2/2020': 0, '3/2020': 0, '4/2020': 0, '5/2020': 0, '6/2020': 0, '7/2020': 0, '8/2020': 0, '9/2020': 0, '10/2020': 0, '11/2020': 0, '12/2020': 0, '1/2021': 0, '2/2021': 0, '3/2021': 0, '4/2021': 0, '5/2021': 0, '6/2021': 0, '7/2021': 0, '8/2021': 0, '9/2021': 0, '10/2021': 0, '11/2021': 0, '12/2021': 0, '1/2022': 0, '2/2022': 0, '3/2022': 0, '4/2022': 0, '5/2022': 0, '6/2022': 0, '7/2022': 0, '8/2022': 0, '9/2022': 0, '10/2022': 0, '11/2022': 0, '12/2022': 0 };
const YEAR_EMPTY = { 2015: 0, 2016: 0, 2017: 0, 2018: 0, 2019: 0, 2020: 0, 2021: 0, 2022: 0 };

export interface Item { name: string; }

export interface SongListItem {
    track_id: string;
    song_name: string;
}

@Component({
    selector: 'app-history',
    templateUrl: './history.component.html',
    styleUrls: ['./history.component.css']
})
export class HistoryComponent implements OnInit {

    afs: AngularFirestore;
    history_docs = {};
    history_items = {};

    /* INFO VARIABLES */
    all_listen_count;
    all_listen_time;
    all_listen_time_unit;
    all_unique_artists;
    all_unique_songs;

    /* GRAPH VARIABLES */
    graph;
    active_dataset_time = "month";
    active_dataset_stat = "counts";
    active_time_unit = {
        "month": "",
        "year": ""
    }
    datasets = {
        "year": {
            "counts": [],
            "times": [],
            "uq_artists": [],
            "uq_songs": []
        },
        "month": {
            "counts": [],
            "times": [],
            "uq_artists": [],
            "uq_songs": []
        }
    }

    labels = {
        "year": ["2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022"],
        "month": ['10/2015', '11/2015', '12/2015', '1/2016', '2/2016', '3/2016', '4/2016', '5/2016', '6/2016', '7/2016', '8/2016', '9/2016', '10/2016', '11/2016', '12/2016', '1/2017', '2/2017', '3/2017', '4/2017', '5/2017', '6/2017', '7/2017', '8/2017', '9/2017', '10/2017', '11/2017', '12/2017', '1/2018', '2/2018', '3/2018', '4/2018', '5/2018', '6/2018', '7/2018', '8/2018', '9/2018', '10/2018', '11/2018', '12/2018', '1/2019', '2/2019', '3/2019', '4/2019', '5/2019', '6/2019', '7/2019', '8/2019', '9/2019', '10/2019', '11/2019', '12/2019', '1/2020', '2/2020', '3/2020', '4/2020', '5/2020', '6/2020', '7/2020', '8/2020', '9/2020', '10/2020', '11/2020', '12/2020', '1/2021', '2/2021', '3/2021', '4/2021', '5/2021', '6/2021', '7/2021', '8/2021', '9/2021', '10/2021', '11/2021', '12/2021', '1/2022', '2/2022', '3/2022', '4/2022', '5/2022', '6/2022', '7/2022', '8/2022', '9/2022', '10/2022', '11/2022', '12/2022']
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
        "uq_artists": {
            "year": "Unique Artists per Year",
            "month": "Unique Artists per Month"
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
        "uq_artists": "Unique Artists",
        "uq_songs": "Unique Songs"
    }

    constructor(afs: AngularFirestore) {
        this.afs = afs;
    }

    ngOnInit() {
        // Subscribe to history
        for (let year in YEAR_EMPTY) {
            this.history_items[String(year)] = {}
            this.history_docs[String(year)] = {}
        }
        for (let month_year in MONTH_EMPTY) {
            let split = month_year.split('/')
            let month = split[0]
            let year = split[1]
            const month_doc = this.afs.doc<Item>('history_' + year + '/' + month)
            this.history_items[year][month] = month_doc.valueChanges()
            this.history_items[year][month].subscribe(val => this.month_subscribe(val, year, month))
        }

        // Init graph
        let canvas = <HTMLCanvasElement>document.getElementById('canvas');
        let context = canvas.getContext('2d');
        this.graph = new Chart(context, {
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

    month_subscribe(val, year, month) {
        this.history_docs[year][month] = val
        this.populate_info()
        this.set_chart_data()
    }

    // Fill in stats about the history
    populate_info() {
        const val = this.history_docs
        var all_listen_count = 0;
        var all_listen_time = 0;
        var all_unique_artists = new Set();
        var all_unique_songs = new Set();
        for (let year in val) {
            for (let month in val[year]) {
                all_listen_count += val[year][month]["listen_count"];
                all_listen_time += val[year][month]["listen_time"];
                val[year][month]["uq_artists"].forEach(artist_id => {
                    all_unique_artists.add(artist_id)
                });
                val[year][month]["uq_songs"].forEach(track_id => {
                    all_unique_songs.add(track_id)
                });
            }
        }
        this.all_listen_count = all_listen_count;
        let transformed_time = this.transform_time(all_listen_time);
        this.all_listen_time = transformed_time[0];
        this.all_listen_time_unit = transformed_time[1];
        this.all_unique_artists = all_unique_artists.size
        this.all_unique_songs = all_unique_songs.size
    }

    // Calculate data for graph
    set_chart_data() {
        const val = this.history_docs
        var year_counts = Object.assign({}, YEAR_EMPTY);
        var year_raw_times = Object.assign({}, YEAR_EMPTY);
        var year_unique_artists = Object.assign({}, YEAR_EMPTY);
        var year_unique_songs = Object.assign({}, YEAR_EMPTY);
        var month_counts = Object.assign({}, MONTH_EMPTY);
        var month_raw_times = Object.assign({}, MONTH_EMPTY);
        var month_unique_artists = Object.assign({}, MONTH_EMPTY);
        var month_unique_songs = Object.assign({}, MONTH_EMPTY);

        for (let year in val) {
            var uq_artists = new Set();
            var uq_songs = new Set();
            for (let month in val[year]) {
                year_counts[year] += val[year][month]["listen_count"];
                year_raw_times[year] += val[year][month]["listen_time"];

                let month_id = month + '/' + year;
                month_counts[month_id] = val[year][month]["listen_count"];
                month_raw_times[month_id] = val[year][month]["listen_time"];
                month_unique_artists[month_id] = val[year][month]["uq_artists"].length
                month_unique_songs[month_id] = val[year][month]["uq_songs"].length
                val[year][month]["uq_artists"].forEach(artist_id => {
                    uq_artists.add(artist_id)
                });
                val[year][month]["uq_songs"].forEach(track_id => {
                    uq_songs.add(track_id)
                });
            }
            year_unique_artists[year] = uq_artists.size
            year_unique_songs[year] = uq_songs.size
        }

        // Calculate time units
        var year_count_data = []
        var year_time_data = []
        var year_unique_artists_data = []
        var year_unique_songs_data = []

        var max_year_time = -1;
        var max_year;
        for (let year in year_raw_times) {
            let year_time = year_raw_times[year]
            if (year_time > max_year_time) {
                max_year_time = year_time;
                max_year = year;
            }
        }
        let year_unit = this.transform_time(max_year_time)[1];
        this.active_time_unit["year"] = year_unit;

        for (let year in year_counts) {
            year_count_data.push(year_counts[year])
        }
        for (let year in year_raw_times) {
            year_time_data.push(this.transform_time_unit(year_raw_times[year], year_unit))
        }
        for (let year in year_unique_artists) {
            year_unique_artists_data.push(year_unique_artists[year])
        }
        for (let year in year_unique_songs) {
            year_unique_songs_data.push(year_unique_songs[year])
        }

        this.datasets["year"]["counts"] = year_count_data;
        this.datasets["year"]["times"] = year_time_data;
        this.datasets["year"]["uq_artists"] = year_unique_artists_data;
        this.datasets["year"]["uq_songs"] = year_unique_songs_data;

        // Calculate month values
        var month_count_data = []
        var month_time_data = []
        var month_unique_artists_data = []
        var month_unique_songs_data = []

        var max_month_time = -1;
        var max_month;
        for (let month in month_raw_times) {
            let month_time = month_raw_times[month]
            if (month_time > max_month_time) {
                max_month_time = month_time;
                max_month = month;
            }
        }
        let month_unit = this.transform_time(max_month_time)[1];
        this.active_time_unit["month"] = month_unit;

        for (let month in month_counts) {
            month_count_data.push(month_counts[month])
        }
        for (let month in month_raw_times) {
            month_time_data.push(this.transform_time_unit(month_raw_times[month], month_unit))
        }
        for (let month in month_unique_artists) {
            month_unique_artists_data.push(month_unique_artists[month])
        }
        for (let month in month_unique_songs) {
            month_unique_songs_data.push(month_unique_songs[month])
        }

        this.datasets["month"]["counts"] = month_count_data;
        this.datasets["month"]["times"] = month_time_data;
        this.datasets["month"]["uq_artists"] = month_unique_artists_data;
        this.datasets["month"]["uq_songs"] = month_unique_songs_data;

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
        }
        else if (unit == "Days") {
            listen_time = listen_time / (60 * 24)
        }
        return listen_time.toFixed(2)
    }

    change_timescale(timescale) {
        this.active_dataset_time = timescale;
        this.graph["data"]["labels"] = this.labels[timescale]
        this.graph["data"]["datasets"][0]["data"] = this.datasets[timescale][this.active_dataset_stat]
        this.graph["options"]["scales"]["xAxes"][0]["scaleLabel"]["labelString"] = this.xlabels[timescale]
        if (this.active_dataset_stat == "times") {
            this.graph["options"]["title"]["text"] = this.active_time_unit[timescale] + this.titles[this.active_dataset_stat][timescale]
        }
        else {
            this.graph["options"]["title"]["text"] = this.titles[this.active_dataset_stat][timescale]
        }
        this.graph.update()
    }

    change_stat(stat) {
        this.active_dataset_stat = stat;
        this.graph["data"]["datasets"][0]["data"] = this.datasets[this.active_dataset_time][stat]
        if (stat == "times") {
            this.graph["options"]["scales"]["yAxes"][0]["scaleLabel"]["labelString"] = this.active_time_unit[this.active_dataset_time]
        }
        else {
            this.graph["options"]["scales"]["yAxes"][0]["scaleLabel"]["labelString"] = this.ylabels[stat]
        }
        if (stat == "times") {
            this.graph["options"]["title"]["text"] = this.active_time_unit[this.active_dataset_time] + this.titles[stat][this.active_dataset_time]
        }
        else {
            this.graph["options"]["title"]["text"] = this.titles[stat][this.active_dataset_time]
        }
        this.graph.update()
    }

}

