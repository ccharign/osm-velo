
var nbÉtapes = 0;
var nbArêtesInterdites = 0;

function gèreLesClics(){
    laCarte.on("click", addMarker);
}


function addMarker(e) {
    if (e.originalEvent.ctrlKey){
	nvArêteInterdite(e);
    }
    else{
	nvÉtape(e);
    }
}


function nvÉtape(e){
    nbÉtapes+=1;
    
    //const markerPlace = document.querySelector(".marker-position");
    //markerPlace.textContent = `new marker: ${e.latlng.lat}, ${e.latlng.lng}`;


    const marker = new L.marker( e.latlng, {
	draggable: true
    })
	  .bindTooltip(""+nbÉtapes, {permanent: true, direction:"bottom"})
	  .addTo(laCarte)
	  .bindPopup(buttonRemove);
    
    marker.numéro = nbÉtapes;
    marker.champ_du_form = "étape_coord"+nbÉtapes
    // var marker = L.marker(props.coords,
    // 			  {icon: myIcon}).bindTooltip(props.country, {permanent: true, direction : 'bottom'}
    // 						     ).addTo(mymap);


    // event remove marker
    marker.on("popupopen", removeMarker);

    // event draged marker
    marker.on("dragend", dragedMarker);

    form = document.getElementById("relance_rapide");
    addHidden(form, marker.champ_du_form, e.latlng.lng +";"+ e.latlng.lat)    
}


function nvArêteInterdite(e){

    // Création du marqueur
    nbArêtesInterdites+=1;
    const marker = new L.marker( e.latlng, {
	draggable: true
    })
	  .addTo(laCarte)
	  .bindPopup(buttonRemove);

    marker.champ_du_form = "interdite_coord"+nbArêtesInterdites;

    // event remove marker
    marker.on("popupopen", removeMarker);

    // event draged marker
    marker.on("dragend", dragedMarker);
    
    // Ajout du champ hidden au formulaire
    form = document.getElementById("relance_rapide");
    addHidden(form, marker.champ_du_form, e.latlng.lng +";"+ e.latlng.lat)    
}


const buttonRemove =
  '<button type="button" class="remove">Supprimer</button>';


// remove marker
function removeMarker() {
    
    const marker = this;// L’objet sur lequelle cette méthode est lancée
    const btn = document.querySelector(".remove");
    
    btn.addEventListener("click", function () {
	//const markerPlace = document.querySelector(".marker-position");
	//markerPlace.textContent = "goodbye marker";
	hidden = document.getElementById(marker.champ_du_form);
	hidden.remove()
	laCarte.removeLayer(marker);
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
    var input = document.createElement('input');
    input.type = 'hidden';
    input.name = key; // 'the key/name of the attribute/field that is sent to the server
    input.value = value;
    input.id = key;
    theForm.appendChild(input);
}
