import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { ArtistsComponent } from './artists/artists.component';
import { CurrentComponent } from './current/current.component';
import { SongsComponent } from './songs/songs.component';
import { SearchComponent } from './search/search.component';


const routes: Routes = [
    { path: '', redirectTo: '/current', pathMatch: 'full' },
    { path: 'artist/:id', component: ArtistsComponent },
    { path: 'current', component: CurrentComponent },
    { path: 'search', component: SearchComponent },
    { path: 'song/:id', component: SongsComponent }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
