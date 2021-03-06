
var nbÉtapes = 0;
var nbArêtesInterdites = 0;

// Ordre des events handler:
// https://stackoverflow.com/questions/2360655/jquery-event-handlers-always-execute-in-order-they-were-bound-any-way-around-t
// [name] is the name of the event "click", "mouseover", ..
// same as you'd pass it to bind()
// [fn] is the handler function
$.fn.bindFirst = function(name, fn) {
    // bind as you normally would
    // don't want to miss out on any jQuery magic
    this.on(name, fn);

    // Thanks to a comment by @Martin, adding support for
    // namespaced events too.
    this.each(function() {
        var handlers = $._data(this, 'events')[name.split('.')[0]];
        // take out the handler we just inserted from the end
        var handler = handlers.pop();
        // move it at the beginning
        handlers.splice(0, 0, handler);
    });
};


function onSelect(e, ui, form, champ){
    // Lancé lors de la sélection d’un élément dans un champ autocomplété.
    // e : l’événement, ui : l’objet sélectionné
    // form : formulaire à modifier
    // Effet : ajoute un champ caché nommé {champ} avec les coords de ui
    lieu = ui.item;
    if (lieu.hasOwnProperty("lon")){
	coords = lieu.lon+";"+lieu.lat;
	form.elements[champ].value=coords;
    }
}


function voir_si_géoLoc(){
    //if (navigator.geolocalisation){
	form_recherche = document.getElementById("recherche");
	addHidden(form_recherche, "localisation", (0.,0.));
	navigator.geolocation.getCurrentPosition(
	    pos => àLaGéoloc(pos, form_recherche),
	    () => pasDeGéoloc(form_recherche)
	);
    //}
}

function àLaGéoloc(pos, form){
    console.log(pos.coords.longitude+";"+pos.coords.latitude);
    form.elements["localisation"].value=pos.coords.longitude+";"+pos.coords.latitude;
}

function pasDeGéoloc(form){
    // Supprime la chekbox « partir de ma position »
    console.log("pas de géoloc");
    form_recherche.getElementsByClassName("checkbox")[0].remove();
}


function gèreLesClics(carte){
    carte.on("click",
	     e => addMarker(e, carte)
	    );
}

function marqueurs_of_form(form, carte){
    
    récupMarqueurs(
	form.elements["marqueurs_é"].value,
	coords => nvÉtape(coords, carte)
    );
    récupMarqueurs(
	form.elements["marqueurs_i"].value,
	coords => nvArêteInterdite(coords, carte)
    );
}


function récupMarqueurs(texte, fonction) {
    // Entrée :
    //     texte contient des coords (chacune de la forme "lon,lat") séparées par un ;
    // Effet : transforme chaque coord en un objet latLng puis lance fonction dessus.
    for (coords_t of (texte.split(";"))){
	if (coords_t){
	    const tab_coords = coords_t.split(",").map(parseFloat);
	    const coord = L.latLng(tab_coords[1], tab_coords[0]);
	    fonction(coord);
	}
    }
}


function addMarker(e, carte) {
    // Appelé lors d’un clic sur la carte leaflet.
    if (e.originalEvent.ctrlKey){
	nvArêteInterdite(e.latlng, carte);
    }
    else{
	nvÉtape(e.latlng, carte);
    }
}




function nvÉtape(latlng, carte){
    nbÉtapes+=1;
    
    //const markerPlace = document.querySelector(".marker-position");
    //markerPlace.textContent = `new marker: ${e.latlng.lat}, ${e.latlng.lng}`;

    
    const marker = new L.marker( latlng, {draggable: true, icon: mon_icone('green'), });
    marker.bindTooltip(""+nbÉtapes, {permanent: true, direction:"bottom"})
	  .addTo(carte)
	  .bindPopup(buttonRemove);
    
    //marker.numéro = nbÉtapes; // Inutile : champ_du_form suffit désormais.
    marker.champ_du_form = "étape_coord"+nbÉtapes;
    // var marker = L.marker(props.coords,
    // 			  {icon: myIcon}).bindTooltip(props.country, {permanent: true, direction : 'bottom'}
    // 						     ).addTo(mymap);


    // event remove marker
    marker.on("popupopen", () => removeMarker(carte, marker));

    // event draged marker
    marker.on("dragend", dragedMarker);

    form = document.getElementById("relance_rapide");
    addHidden(form, marker.champ_du_form, latlng.lng +";"+ latlng.lat);
}


function nvArêteInterdite(latlng, carte){

    // Création du marqueur
    nbArêtesInterdites+=1;
    const marker = new L.marker( latlng, {
	icon: mon_icone('red'),
	draggable: true
    })
	  .addTo(carte)
	  .bindPopup(buttonRemove);

    marker.champ_du_form = "interdite_coord"+nbArêtesInterdites;

    // event remove marker
    marker.on("popupopen", () => removeMarker(carte, marker));

    // event draged marker
    marker.on("dragend", dragedMarker);
    
    // Ajout du champ hidden au formulaire
    form = document.getElementById("relance_rapide");
    addHidden(form, marker.champ_du_form, latlng.lng +";"+ latlng.lat);
}


const buttonRemove =
  '<button type="button" class="remove">Supprimer</button>';


// remove marker
function removeMarker(carte, marker) {
    
    //const marker = this;// L’objet sur lequelle cette méthode est lancée
    const btn = document.querySelector(".remove");
    
    btn.addEventListener("click", function () {
	//const markerPlace = document.querySelector(".marker-position");
	//markerPlace.textContent = "goodbye marker";
	hidden = document.getElementById(marker.champ_du_form);
	hidden.remove();
	carte.removeLayer(marker);
    });
}


// draged
function dragedMarker() {
  //const markerPlace = document.querySelector(".marker-position");
  //markerPlace.textContent = `change position: ${this.getLatLng().lat}, ${
  //  this.getLatLng().lng
    //}`;
    const marker=this;
    document.getElementById(marker.champ_du_form).value = marker.getLatLng().lng+";"+ marker.getLatLng().lat;
}


function addHidden(theForm, key, value) {
    // Create a hidden input element, and append it to the form:
    console.log(`Je crée un hidden. this : ${this}, form: ${theForm}, key:${key}`);
    var input = document.createElement('input');
    input.type = 'hidden';
    input.name = key; // 'the key/name of the attribute/field that is sent to the server
    input.value = value;
    input.id = key;
    theForm.appendChild(input);
}
