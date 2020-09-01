import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { ArtistsComponent } from './artists/artists.component';
import { CurrentComponent } from './current/current.component';
import { SongsComponent } from './songs/songs.component';
import { SearchComponent } from './search/search.component';
import { HistoryComponent } from './history/history.component';


const routes: Routes = [
    { path: '', redirectTo: '/current', pathMatch: 'full' },
    { path: 'artist/:id', component: ArtistsComponent },
    { path: 'current', component: CurrentComponent },
    { path: 'history', component: HistoryComponent },
    { path: 'search', component: SearchComponent },
    { path: 'song/:id', component: SongsComponent }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
