(function ($) {
    'use strict';
    $(function() {

	window.getCookie = function(name){
	    var cookieValue = null;
	    if (document.cookie && document.cookie != '') {
		var cookies = document.cookie.split(';');
		for (var i = 0; i < cookies.length; i++) {
		    var cookie = $.trim(cookies[i]);
		    // Does this cookie string begin with the name we want?
		    if (cookie.substring(0, name.length + 1) == (name + '=')) {
			cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
			break;
		    }
		}
	    }
	    return cookieValue;
	}

	window.csrfSafeMethod = function(method){
	    // these HTTP methods do not require CSRF protection
	    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
	}

	window.sameOrigin = function(url){
	    // test that a given url is a same-origin URL
	    // url could be relative or scheme relative or absolute
	    var host = document.location.host; // host + port
	    var protocol = document.location.protocol;
	    var sr_origin = '//' + host;
	    var origin = protocol + sr_origin;
	    // Allow absolute or scheme relative URLs to same origin
	    return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
		(url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
		// or any other URL that isn't scheme relative or absolute i.e relative.
		!(/^(\/\/|http:|https:).*/.test(url));
	}

	$.ajaxSetup({
	    beforeSend: function(xhr, settings) {
		if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
		    // Send the token to same-origin, relative URLs only.
		    // Send the token only if the method warrants CSRF protection
		    // Using the CSRFToken value acquired earlier
		    xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
		}
	    }
	});


	if (typeof String.prototype.startsWith != 'function') {
	    String.prototype.startsWith = function (str){
		return this.indexOf(str) == 0;
	    };
	}
	if (typeof String.prototype.endsWith != 'function') {
	    String.prototype.endsWith = function(suffix) {
		return this.indexOf(suffix, this.length - suffix.length) !== -1;
	    };
	}

	/* Init the graph view if we have graph-view preview boxes */
	if($('.iobject-graph').length > 0){
	    $.each($('.iobject-graph'), function(){
		var graph_box = $(this),
		    graph_canvas = graph_box.find('.iobject-graph-canvas').first();
		
		
		// Callback function for rendering graph/tree
		var BAKrender_graph = function(gdata){
		    graph_box.toggle(); // Show the box. Needed to get the canvas dimensions
		    gdata = gdata.d;

		    var nodes = {},
		        links = [],
		        width = graph_canvas.width(),
		        height  = graph_canvas.height(),
		        duration = 300,
		        rectW = 60,
		        rectH = 30;

		    // Compute the nodes and the links.
		    gdata.forEach(function(link) {
			if(!(link.source in nodes)){
			    nodes[link.source] = {}
			    $.each(link, function(i,v){
				if(i.startsWith('source_'))
				    nodes[link.source][i.replace('source_', '')] = v;
			    });
			}
			if(!(link.dest in nodes)){
			    nodes[link.dest] = {}
			    $.each(link, function(i,v){
				if(i.startsWith('dest_'))
				    nodes[link.dest][i.replace('dest_', '')] = v;
			    });
			}
		    });
		    gdata.forEach(function(link) {
			links.push({source: nodes[link.source], target: nodes[link.dest]});
		    });


		    var svg = d3.select(graph_canvas.get(0))
			.append("svg:svg")
		    	  .attr("width", width)
			  .attr("height", height)
			  .attr("pointer-events", "all")
		    	.append("svg:g")
			  .call(d3.behavior.zoom().on("zoom", redraw))
			.append('svg:g');

		    svg.append('svg:rect')
			.attr('width', 2*width)
			.attr('height', 2*height)
			.attr('fill', 'white');

		    function redraw() {
			svg.attr("transform",
				 "translate(" + d3.event.translate + ")"
				 + " scale(" + d3.event.scale + ")");
		    }


		    var force = d3.layout.force()
			.nodes(d3.values(nodes))
			.links(links)
			.size([width, height])
			.linkDistance(60)
			.charge(-300)
			.on("tick", tick)
			.size([width, height])
			.start();

		    var link = svg.selectAll(".link")
			.data(force.links())
			.enter().append("line")
			.attr("class", "link");

		    var node = svg.selectAll(".node")
			.data(force.nodes())
			.enter().append("g")
			.attr("class", "node");

		    node.append("circle")
			.attr("r", 8)
			.style("fill", function(d){

			});

		    node.append("text")
			.attr("x", 12)
			.attr("dy", ".35em")
			.text(function(d) { return d.name; });

		    function tick() {
			link
			    .attr("x1", function(d) { return d.source.x; })
			    .attr("y1", function(d) { return d.source.y; })
			    .attr("x2", function(d) { return d.target.x; })
			    .attr("y2", function(d) { return d.target.y; });

			node
			    .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });
		    }

		    //force.start();
		    //for (var i = 0; i < 400; ++i) force.tick();
		    //force.stop();


		}; // End render_graph()







		// Callback function for rendering graph/graph
		var BAK1_render_graph = function(gdata){
		    graph_box.toggle(); // Show the box. Needed to get the canvas dimensions

		    var nodes = {},
		        links = [],
		        width = graph_canvas.width(),
		        height  = graph_canvas.height(),
		        duration = 300,
		        root_id = gdata.node_id,
		        linkedByIndex = {};

		    node_data = gdata.nodes;
		    edge_data = gdata.edges;
		    // Compute the nodes and the links.
		    node_data.forEach(function(node) {
			if(!(node[0] in nodes)){
			    nodes[link.source] = {}
			    if(node[0] == root_id)
				nodes[node[0]]['fixed'] = true;
			    $.each(node[1], function(i,v){
				    nodes[node[0]][i] = v;
			    });
			    nodes[node[0]]['id'] = node[0];
			}

		    });
		    edge_data.forEach(function(edge) {
			links.push({source: nodes[edge[0]], target: nodes[edge[1]]});
			linkedByIndex[edge[0] + ',' + edge[1]] = 1;
		    });

		    function isConnected(a, b) {
			return linkedByIndex[a.id + "," + b.id] || linkedByIndex[b.id + "," + a.id] || a.id == b.id;
		    }


		    var svg = d3.select(graph_canvas.get(0))
			.append("svg:svg")
		    	  .attr("width", width)
			  .attr("height", height)
			  .attr("pointer-events", "all")
		    	.append("svg:g")
			  .call(d3.behavior.zoom().on("zoom", redraw))
			.append('svg:g');

		    svg.append('svg:rect')
			.attr('width', 2*width)
			.attr('height', 2*height)
			.attr('fill', 'white');

		    function redraw() {
			svg.attr("transform",
				 "translate(" + d3.event.translate + ")"
				 + " scale(" + d3.event.scale + ")");
		    }


		    var force = d3.layout.force()
			.nodes(d3.values(nodes))
			.links(links)
			.size([width, height])
			.linkDistance(40)
			.charge(-800)
			.on("tick", tick)
			.size([width, height])
			.start();

		    var link = svg.selectAll(".link")
			.data(force.links())
			.enter().append("line")
			.attr("class", "link");

		    var node = svg.selectAll(".node")
			.data(force.nodes())
			.enter().append("g")
			.attr("class", "node")
			.each(function(d) {
			    var t = d3.select(this);
			    var t_core = false;
			    switch(d.iobject_type){
			    case 'STIX_Package':
				t_core = t.append("image")
				    .attr("xlink:href", "/static/img/stix/stix.png")
		     		    .attr("x", -15)
		     		    .attr("y", -15)
		     		    .attr("width", 30)
		     		    .attr("height", 30);
				break;
			    case 'TTP':
				t_core = t.append("image")
				    .attr("xlink:href", "/static/img/stix/ttp.svg")
		     		    .attr("x", -8)
		     		    .attr("y", -8)
		     		    .attr("width", 16)
		     		    .attr("height", 16);
				break;
			    case 'ThreatActor':
				t_core = t.append("image")
				    .attr("xlink:href", "/static/img/stix/threat_actor.svg")
		     		    .attr("x", -8)
		     		    .attr("y", -8)
		     		    .attr("width", 16)
		     		    .attr("height", 16);
				break;
			    default:
				t_core = t.append("circle")
				    .attr("r", 10);

			    }

			    t_core.on('mouseover', fade(.1))
				.on('mouseout', fade(1));

			    t.append("text")
		    	    	.attr("x", 12)
		    	    	.attr("dy", ".35em")
				.attr('opacity', '0')
		    	    	.text(function(d) { return d.name; });

			});


		    function fade(opacity) {
			return function(d) {
			    node.style("stroke-opacity", function(o) {
				var thisOpacity = isConnected(d, o) ? 1 : opacity;

				if(opacity==1){
				    d3.select(this).selectAll('[opacity="1"]')
					.attr('opacity', '0');

				}else{
				    d3.select(this).selectAll('[opacity="0"]')
					.attr('opacity', '1');
				}

 				this.setAttribute('fill-opacity', thisOpacity);
				return thisOpacity;
			    });

			    link.style("stroke-opacity", opacity).style("stroke-opacity", function(o) {
				return o.source === d || o.target === d ? 1 : opacity;
			    });
			};
		    }


		    function tick(e) {
			// var kx = .4 * e.alpha, ky = 1.4 * e.alpha;
			//     links.forEach(function(d, i) {
			//       d.target.x += (d.source.x - d.target.x) * kx;
			//       d.target.y += (d.source.y + 80 - d.target.y) * ky;
			//     });

			link
			    .attr("x1", function(d) { return d.source.x; })
			    .attr("y1", function(d) { return d.source.y; })
			    .attr("x2", function(d) { return d.target.x; })
			    .attr("y2", function(d) { return d.target.y; });

			node
			    .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });
		    }
		}; // End render_graph()










		// Callback function for rendering graph/graph
		var render_graph = function(gdata){
		    graph_box.toggle(); // Show the box. Needed to get the canvas dimensions

		    var nodes = {},
		        links = [],
		        width = graph_canvas.width(),
		        height  = graph_canvas.height(),
		        duration = 300,
		        root_id = gdata.node_id,
		        linkedByIndex = {},
		        self_index = 0;

		    gdata = gdata.d;

		    // Compute the nodes and the links.
		    gdata.forEach(function(link) {
		    	if(!(link.source in nodes)){
		    	    nodes[link.source] = {}
		    	    if(link.source == root_id)
		    		nodes[link.source]['fixed'] = true;
		    	    $.each(link, function(i,v){
		    		if(i.startsWith('source_'))
		    		    nodes[link.source][i.replace('source_', '')] = v;
		    	    });
		    	    nodes[link.source]['id'] = link.source;
		    	}
		    	if(!(link.dest in nodes)){
		    	    nodes[link.dest] = {}
		    	    if(link.dest == root_id)
		    		nodes[link.dest]['fixed'] = true;
		    	    $.each(link, function(i,v){
		    		if(i.startsWith('dest_'))
		    		    nodes[link.dest][i.replace('dest_', '')] = v;
		    	    });
		    	    nodes[link.dest]['id'] = link.dest;
		    	}
		    });
		    gdata.forEach(function(link) {
			if(link.direction=='up')
			    links.push({target: nodes[link.source], source: nodes[link.dest]});
			else
			    links.push({source: nodes[link.source], target: nodes[link.dest]});
			linkedByIndex[link.source + ',' + link.dest] = 1;
		    });

		    function isConnected(a, b) {
			return linkedByIndex[a.id + "," + b.id] || linkedByIndex[b.id + "," + a.id] || a.id == b.id;
		    }


		    var svg = d3.select(graph_canvas.get(0))
			.append("svg:svg")
		    	  .attr("width", width)
			  .attr("height", height)
			  .attr("pointer-events", "all")
		    	.append("svg:g")
			  .call(d3.behavior.zoom().on("zoom", zoom))
			.append('svg:g');

		    svg.append('svg:rect')
			.attr('width', 2*width)
			.attr('height', 2*height)
			.attr('fill', 'white')
			.attr('transform', 'translate(' + (-width/2) + ',' + (-height/2) + ')');

		    svg.append("svg:defs").selectAll("marker")
			.data(["end"])
			.enter().append("svg:marker")
			.attr("id", String)
			.attr("viewBox", "0 -5 10 10")
			.attr("refX", 21)
			.attr("refY", 0)
			.attr("markerWidth", 5)
			.attr("markerHeight", 5)
			.attr("orient", "auto")
			.append("svg:path")
			.attr("d", "M0,-5L10,0L0,5");

		    function zoom() {
			svg.attr("transform",
				 "translate(" + d3.event.translate + ")"
				 + " scale(" + d3.event.scale + ")");
			svg.selectAll('.toggle-hover').attr('transform', 'scale('+ 1/d3.event.scale +')')
		    }


		    var force = d3.layout.force()
			.nodes(d3.values(nodes))
			.links(links)
			.size([width, height])
			.linkDistance(25)
			.charge(-1500)
			.on("tick", tick)
			.size([width, height]);


		    var link = svg.selectAll(".link")
			.data(force.links())
			.enter().append("path")
			.attr("class", "link")
			.attr('marker-end', 'url(#end)');

		    var node = svg.selectAll(".node")
			.data(force.nodes())
			.enter().append("g")
			.attr("class", "node")
			.each(function(d, i) {
			    var t = d3.select(this);
			    var t_core = false;
			    
			    if(d.iobject_type == 'STIX_Package'){
				t_core = t.append("image")
				    .attr("xlink:href", "/static/img/stix/stix.png")
		     		    .attr("x", -15)
		     		    .attr("y", -15)
		     		    .attr("width", 30)
		     		    .attr("height", 30);
			    }else if(d.iobject_type == 'TTP'){
				t_core = t.append("image")
				    .attr("xlink:href", "/static/img/stix/ttp.svg")
		     		    .attr("x", -8)
		     		    .attr("y", -8)
		     		    .attr("width", 16)
		     		    .attr("height", 16);
			    }else if(d.iobject_type == 'ThreatActor'){
				t_core = t.append("image")
				    .attr("xlink:href", "/static/img/stix/threat_actor.svg")
		     		    .attr("x", -8)
		     		    .attr("y", -8)
		     		    .attr("width", 16)
		     		    .attr("height", 16);
			    }else if(d.iobject_type == 'Observable'){
				t_core = t.append("image")
				    .attr("xlink:href", "/static/img/stix/observable.svg")
		     		    .attr("x", -8)
		     		    .attr("y", -8)
		     		    .attr("width", 16)
		     		    .attr("height", 16);
			    }else if(d.iobject_type == 'Indicator'){
				t_core = t.append("image")
				    .attr("xlink:href", "/static/img/stix/indicator.svg")
		     		    .attr("x", -8)
		     		    .attr("y", -8)
		     		    .attr("width", 16)
		     		    .attr("height", 16);
			    }else if(d.iobject_type == 'Marking'){
				t_core = t.append("image")
				    .attr("xlink:href", "/static/img/stix/data_marking.svg")
		     		    .attr("x", -8)
		     		    .attr("y", -8)
		     		    .attr("width", 16)
		     		    .attr("height", 16);
			    }else if(d.iobject_type == 'Campaign'){
				t_core = t.append("image")
				    .attr("xlink:href", "/static/img/stix/campaign.svg")
		     		    .attr("x", -8)
		     		    .attr("y", -8)
		     		    .attr("width", 16)
		     		    .attr("height", 16);
			    }else{
				t_core = t.append("circle")
				    .attr("r", 10);
			    }


			    t_core.on('mouseover', fade(.3, 'over'))
				.on('mouseout', fade(1, 'out'))
				.on('click', node_click);

			    t.append('rect')
			    	.attr('class', 'toggle-hover')
			    	.attr('height' , '14px')
			    	.attr('fill', '#ddd')
		    	    	.attr("x", 10)
			    	.attr("opacity", "0");
			    
			    t.append("text")
			    	.attr("class", "toggle-hover")
		    	    	.attr("x", 12)
			    	.attr("y", 7)
		    	    	.attr("dy", ".35em")
			    	.attr("opacity", "0")
		    	    	.text(function(d) { return d.name; });

			    if(d.fixed){
				self_index = i;
				t_core = t.insert("circle", ":first-child")
				    .attr("r", 15)
				    .attr('style', 'fill:red;stroke-width:0;')
				    .attr('opacity', '.3');
			    }
			});

		    function node_click(e){
			var el = $('.iobject-graph .details-box').first(),
			    img = $(this).attr('href');
,
			
			el.find('.title').text(e.iobject_type + ': ' + e.name);
			el.find('img').attr('src', img);
			var itmpl = '<table><tbody> \
			      <tr><td>NS:</td> <td>'+ e.identifier_ns +'</td></tr> \
			      <tr><td>ID:</td> <td>'+ e.identifier_uid +'</td></tr> \
			      <tr><td>Link:</td> <td><a href="'+ e.url +'">'+ e.id +'</a></td></tr> \
			      </tbody></table> \
                        ';
			el.find('.desc').html(itmpl);

			el.find('.ui-icon-close').click(function(){
			     $(this).parent().hide();
			});

			el.show();
		    }


		    function fade(opacity, oo) {
			return function(d) {
			    node.style("stroke-opacity", function(o) {
				var thisOpacity = isConnected(d, o) ? 1 : opacity;

				if(oo=='out' && isConnected(d, o)){
				    d3.select(this).selectAll('.toggle-hover')
					.attr('opacity', '0')
					.attr('stroke-opacity', '0')
					.attr('fill-opacity', '0');

				}
				if(oo=='over' && isConnected(d, o)){
				    d3.select(this).selectAll('.toggle-hover')
					.attr('opacity', '1')
					.attr('stroke-opacity', '1')
					.attr('fill-opacity', '1');

				    // fix the rect backround of the text label
				    var lbl = d3.select(this).selectAll('text.toggle-hover')[0].pop();
				    d3.select(this).selectAll('rect.toggle-hover')
					.attr('width', function(){
					    if(lbl.getBBox().width > 0)
						return lbl.getBBox().width + 5
					    return 0;
					});
				    

				}

 				this.setAttribute('fill-opacity', thisOpacity); //element itself
				d3.select(this).selectAll('image').attr('opacity', thisOpacity);
				return thisOpacity;
			    });

			    link.style("opacity", function(o) {
				return o.source === d || o.target === d ? 1 : opacity;
			    });

			};
		    }


		    function tick(e) {
			// var kx = .4 * e.alpha, ky = 1.4 * e.alpha;
			//     links.forEach(function(d, i) {
			//       d.target.x += (d.source.x - d.target.x) * kx;
			//       d.target.y += (d.source.y + 80 - d.target.y) * ky;
			//     });


			node.attr("transform", function(d) { 
			    
			    if(d.index==self_index){
				d.x = width/2;
				d.y = height/2;
			    }

			    var r = d.name.length;
			    //these setting are used for bounding box, see [http://blockses.appspot.com/1129492][1]
			    d.x = Math.max(r, Math.min(width - r, d.x));
			    d.y = Math.max(r, Math.min(height - r, d.y));

			    return "translate("+d.x+","+d.y+")";            

			});

        		link.attr("d", function(d) {
			    var dx = d.target.x - d.source.x,
			    dy = d.target.y - d.source.y;
			    return "M" + d.source.x + "," + d.source.y + " " + d.target.x + "," + d.target.y;
			});

		    }


		    force.start();
		    for(var i=0; i<400; i++){
		    	force.tick();
		    }
		    force.stop();
		    
		}; // End render_graph()



		var render_tree = function(graph_data){
		    graph_box.toggle(); // Show the box. Needed to get the canvas dimensions

		    var gdata = [],
		        width = graph_canvas.width(),
		        height  = graph_canvas.height(),
		        duration = 300,
		        rectW = 60,
		        rectH = 30,
		        linkLength = 150,
		        i=0, zm;


		    // Prepare the data for tree display
		    var idtoNodemap = {},
		        root = null;
		    (graph_data.d).forEach(function(data) {
			if(!(data.source in idtoNodemap)){
			    idtoNodemap[data.source] = {}
			    $.each(data, function(i,v){
				if(i.startsWith('source_'))
				    idtoNodemap[data.source][i.replace('source_', '')] = v;
			    });
			    idtoNodemap[data.source]['children'] = [];
			    idtoNodemap[data.source]['parents'] = [];
			}
			if(!(data.dest in idtoNodemap)){
			    idtoNodemap[data.dest] = {}
			    $.each(data, function(i,v){
				if(i.startsWith('dest_'))
				    idtoNodemap[data.dest][i.replace('dest_', '')] = v;
			    });
			    idtoNodemap[data.dest]['children'] = [];
			    idtoNodemap[data.dest]['parents'] = [];
			}
			
			// Set children
			idtoNodemap[data.source]['children'].push(idtoNodemap[data.dest]);
			// Set parents
			idtoNodemap[data.dest]['parents'].push(idtoNodemap[data.source]);
			
		    });
		    //find the root (the one with no parents( we take the first))
		    $.each(idtoNodemap, function(i,v){
			if($.isEmptyObject(v['parents'])){
			    root = idtoNodemap[i];
			    return false;
			}
		    });


		    var svg = d3.select(graph_canvas.get(0)).append("svg")
			.attr("width", width).attr("height", height)
		    	.call(zm = d3.behavior.zoom().scaleExtent([.5,5]).on("zoom", redraw)).append("g")
			//.attr("transform", "translate(" + 350 + "," + 20 + ")");
			.attr("transform", "translate(" + (width/2 - rectW/2) + "," + 20 + ")");
		    zm.translate([(width/2 - rectW/2), 20]);

		    var graph = d3.layout.tree().nodeSize([70, 40]);
		    var diagonal = d3.svg.diagonal()
			.projection(function (d) {
			    return [d.x + rectW / 2, d.y + rectH / 2];
			});

		    //Redraw for zoom
		    function redraw() {
			svg.attr("transform",
				 "translate(" + d3.event.translate + ")"
				 + " scale(" + d3.event.scale + ")");
		    }



		    function collapse(d) {
			if (d.children) {
			    d._children = d.children;
			    d._children.forEach(collapse);
			    d.children = null;
			}
		    }

		    function update(source) {

			// Compute the new graph layout.
			var nodes = graph.nodes(root).reverse(),
			links = graph.links(nodes);

			// Normalize for fixed-depth.
			nodes.forEach(function (d) {
			    d.y = d.depth * linkLength;
			});

			// Update the nodes…
			var node = svg.selectAll("g.node")
			    .data(nodes, function (d) {
				return d.id || (d.id = ++i);
			    });

			// Enter any new nodes at the parent's previous position.
			var nodeEnter = node.enter().append("g")
			    .attr("class", "node")
			    .attr("transform", function (d) {
				return "translate(" + source.x0 + "," + source.y0 + ")";
			    })
			    .on("click", click);

			nodeEnter.append("rect")
			    .attr("width", rectW)
			    .attr("height", rectH)
			    .attr("stroke", "black")
			    .attr("stroke-width", 1)
			    .style("fill", function (d) {
				return d._children ? "lightsteelblue" : "#fff";
			    });

			nodeEnter.append("text")
			    .attr("x", rectW / 2)
			    .attr("y", rectH / 2)
			    .attr("dy", ".35em")
			    .attr("text-anchor", "middle")
			    .text(function (d) {
				return d.name;
			    });

			// Transition nodes to their new position.
			var nodeUpdate = node.transition()
			    .duration(duration)
			    .attr("transform", function (d) {
				return "translate(" + d.x + "," + d.y + ")";
			    });

			nodeUpdate.select("rect")
			    .attr("width", rectW)
			    .attr("height", rectH)
			    .attr("stroke", "black")
			    .attr("stroke-width", 1)
			    .style("fill", function (d) {
				return d._children ? "lightsteelblue" : "#fff";
			    });

			nodeUpdate.select("text")
			    .style("fill-opacity", 1);

			// Transition exiting nodes to the parent's new position.
			var nodeExit = node.exit().transition()
			    .duration(duration)
			    .attr("transform", function (d) {
				return "translate(" + source.x + "," + source.y + ")";
			    })
			    .remove();

			nodeExit.select("rect")
			    .attr("width", rectW)
			    .attr("height", rectH)
			//.attr("width", bbox.getBBox().width)""
			//.attr("height", bbox.getBBox().height)
			    .attr("stroke", "black")
			    .attr("stroke-width", 1);

			nodeExit.select("text");

			// Update the links…
			var link = svg.selectAll("path.link")
			    .data(links, function (d) {
				return d.target.id;
			    });

			// Enter any new links at the parent's previous position.
			link.enter().insert("path", "g")
			    .attr("class", "link")
			    .attr("x", rectW / 2)
			    .attr("y", rectH / 2)
			    .attr("d", function (d) {
				var o = {
				    x: source.x0,
				    y: source.y0
				};
				return diagonal({
				    source: o,
				    target: o
				});
			    });

			// Transition links to their new position.
			link.transition()
			    .duration(duration)
			    .attr("d", diagonal);

			// Transition exiting nodes to the parent's new position.
			link.exit().transition()
			    .duration(duration)
			    .attr("d", function (d) {
				var o = {
				    x: source.x,
				    y: source.y
				};
				return diagonal({
				    source: o,
				    target: o
				});
			    })
			    .remove();

			// Stash the old positions for transition.
			nodes.forEach(function (d) {
			    d.x0 = d.x;
			    d.y0 = d.y;
			});
		    }

		    // Toggle children on click.
		    function click(d) {
			if (d.children) {
			    d._children = d.children;
			    d.children = null;
			} else {
			    d.children = d._children;
			    d._children = null;
			}
			update(d);
		    }


		    root.x0 = 0;
		    root.y0 = height / 2;
		    root.children.forEach(collapse);
		    update(root);
		    

		}; // End render_tree()




		// Load graph data from backend
		$.getJSON('graph', function(data){
		    if(data.status){
			//render_tree(data.data);
			render_graph(data.data);
		    }else{
			//Error fetching graph data
		    }
		});

	    });
	}



    });
}(django.jQuery)); // Reuse django injected jQuery library
