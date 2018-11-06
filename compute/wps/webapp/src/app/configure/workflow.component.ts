import { Component, Input, OnInit, AfterViewInit, ViewEncapsulation, ViewChild } from '@angular/core';

import { Parameter } from './parameter';
import { ConfigureService } from './configure.service';
import { Process } from './process';
import { NotificationService } from '../core/notification.service';
import { ConfigService } from '../core/config.service';
import { WPSService } from '../core/wps.service';
import { ProcessWrapper } from './process-wrapper';
import { Link } from './link';
import { EditorState } from './editor-state.enum';
import { Variable } from './variable';
import { RegridModel } from './regrid.component';

import * as d3 from 'd3';

declare var $: any;

@Component({
  selector: 'workflow',
  encapsulation: ViewEncapsulation.None,
  styles: [`
  svg {
    border: 1px solid #ddd;
  }

  .error {
    stroke: #ff0000!important;
  }

  .pane {
    padding: 1em;
  }

  .graph-container {
    width: 100%;
    min-height: calc(100vh - 100px);
  }

  .fill {
    min-height: calc(100vh - 100px);
  }

  .node {
    fill: #ddd;
    stroke: white;
    stroke-width: 2px;
  }

  .node-select {
    fill: #abd8ff;
  }

  .node-connect {
    fill: #ccc!important;
  }

  .link {
    stroke: black;
    stroke-width: 3px;
    marker-end: url(#end-arrow);
  }

  .link-select {
    stroke: #abd8ff!important;
  }

  .link-drag {
    stroke: black;
    stroke-width: 3px;
    marker-end: url(#drag-end-arrow);
  }

  .list-item-axis {
    padding: 5px;
  }

  .select-spacer {
    margin-bottom: 10px;
  }

  .loading {
    cursor: wait;
  }
  `],
  templateUrl: './workflow.component.html'
})
export class WorkflowComponent implements OnInit, AfterViewInit {
  @Input() datasetID: string[];
  @Input() params: any;

  processes: string[];

  nodes: ProcessWrapper[];
  links: Link[];
  selectedNode: ProcessWrapper;

  state: EditorState;
  stateData: any;

  regrid: RegridModel = new RegridModel();
  parameters: Parameter[] = [];

  svg: any;
  svgLinks: any;
  svgNodes: any;
  svgDrag: any;

  constructor(
    private configureService: ConfigureService,
    private configService: ConfigService,
    private notificationService: NotificationService,
    private wpsService: WPSService,
  ) { 
    this.nodes = [];

    this.links = [];

    this.state = EditorState.None;

    this.wpsService.getCapabilities('/wps/')
      .then((processes: string[]) => this.processes = processes);
  }

  ngOnInit() {
    d3.select(window)
      .on('keydown', () => this.removeElements())

    this.svg = d3.select('.graph-container')
      .on('mouseover', () => this.svgMouseOver());

    this.svg.append('svg:defs')
      .append('svg:marker')
      .attr('id', 'end-arrow')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 42)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('svg:path')
      .attr('d', 'M0,-5L10,0L0,5');

    this.svg.append('svg:defs')
      .append('svg:marker')
      .attr('id', 'drag-end-arrow')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 0)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('svg:path')
      .attr('d', 'M0,-5L10,0L0,5');

    let graph = this.svg.append('g')
      .classed('graph', true);

    this.svgDrag = graph.append('svg:path')
      .attr('class', 'link-drag hidden')
      .attr('d', 'M0,0L0,0');

    this.svgLinks = graph.append('g')
      .classed('links', true);

    this.svgNodes = graph.append('g')
      .classed('nodes', true);
  }

  ngAfterViewInit() {
    $('#processConfigureModal').on('hidden.bs.modal', (e: any) => {
      this.update();
    });
  }

  removeElements() {
    switch (d3.event.keyCode) {
      case 8:
      case 46: {
        let selectedLinks = this.svgLinks.selectAll('.link-select');

        selectedLinks.each((d: any, i: number, g: any) => {
          this.links = this.links.filter((item: Link) => item != d);
        });

        selectedLinks = selectedLinks.data(this.links, (item: Link) => item.uid);

        selectedLinks.exit().remove();
      }
      break;
    }
  }

  removeInput(item: Variable|Process) {
    if (item instanceof Process) {
      this.links = this.links.filter((x: Link) => {
        if (x.src.process == item || x.dst.process == item) {
          return false;
        }

        return true;
      });
    } else {
      throw new Error('Removing something other than a process');
    }

    this.update();
  }

  removeNode(node: ProcessWrapper) {
    $('#configure').modal('hide');

    this.links = this.links.filter((value: Link) => {
      return value.src.uid() !== node.uid() && value.dst.uid() !== node.uid();
    });

    this.nodes = this.nodes.filter((value: ProcessWrapper) => { 
      return node.uid() !== value.uid();
    });

    this.selectedNode = node = null;

    this.update();
  }

  dropped(event: any) {
    this.state = EditorState.Dropped;

    this.stateData = event.dragData;
  }

  svgMouseOver() {
    if (this.state === EditorState.Dropped) {
      this.state = EditorState.None;

      let origin = d3.mouse(d3.event.target);

      let process = new Process(this.stateData);

      this.wpsService.describeProcess('/wps/', process.identifier)
        .then((description: any) => {
          process.description = description;
        });

      this.nodes.push(new ProcessWrapper(process, origin[0], origin[1]));

      this.update();
    }
  }

  nodeClick() {
    this.selectedNode = <ProcessWrapper>d3.select(d3.event.target).datum();

    $('#processConfigureModal').modal('show');
  }

  nodeMouseEnter() {
    if (this.state === EditorState.Connecting) {
      this.stateData.dst = d3.select(d3.event.target).datum();
    }

    d3.select(d3.event.target)
      .select('circle')
      .classed('node-connect', true);
  }

  nodeMouseLeave() {
    if (this.state === EditorState.Connecting) {
      this.stateData.dst = null;
    }

    d3.select('.node-connect')
      .classed('node-connect', false);
  }

  drag() {
    let node = d3.event.subject;

    if (this.state === EditorState.Connecting) {
      this.svgDrag
        .attr('d', `M${node.x},${node.y}L${d3.event.x},${d3.event.y}`);
    } else {
      node.x += d3.event.dx;

      node.y += d3.event.dy;

      this.update();
    }
  }

  dragStart() {
    if (d3.event.sourceEvent.shiftKey) {
      let node = d3.event.sourceEvent;
      let process = <ProcessWrapper>d3.select(node.target).datum();

      this.state = EditorState.Connecting;

      this.stateData = new Link(process);

      this.svgDrag
        .attr('d', `M${node.x},${node.y}L${node.x},${node.y}`)
        .classed('hidden', false);
    }
  }

  dragEnd() {
    if (this.state === EditorState.Connecting) {
      d3.select('.node-connect')
        .classed('node-connect', false);

      this.svgDrag.classed('hidden', true);

      if (this.stateData !== null && this.stateData.dst !== null) {
        let exists = this.links.findIndex((link: Link) => {
          return link.src === this.stateData.src && link.dst === this.stateData.dst;
        });

        if (exists === -1) {
          let src = this.stateData.src,
            dst = this.stateData.dst;

          dst.process.inputs.push(src.process);

          this.links.push(this.stateData);

          this.update();
        }
      }

      this.state = EditorState.None;

      this.stateData = null;
    }
  }
  
  update() {
    let links = this.svgLinks
      .selectAll('path')
      .attr('d', (d: any) => {
        return 'M' + d.src.x + ',' + d.src.y + 'L' + d.dst.x + ',' + d.dst.y;
      })
      .data(this.links, (item: Link) => { return item.uid; });

    links.exit().remove();

    links.enter()
      .append('path')
      .classed('link', true)
      .attr('d', (d: any) => {
        return 'M' + d.src.x + ',' + d.src.y + 'L' + d.dst.x + ',' + d.dst.y;
      })
      .on('click', (data: any, index: any, group: any) => {
        let link = d3.select(group[index]);

        if (link.classed('link-select')) {
          link.classed('link-select', false);
        } else {
          link.classed('link-select', true);
        }
      });;

    let nodes = this.svgNodes
      .selectAll('g')
      .attr('transform', (d: any) => { return `translate(${d.x}, ${d.y})`; })
      .data(this.nodes, (item: ProcessWrapper) => { return item.uid(); });

    // Update the error class on circles
    this.svgNodes
      .selectAll('circle')
      .classed('error', (d: ProcessWrapper) => {
        return d.errors;
      });

    nodes.exit().remove();

    let newNodes = nodes.enter()
      .append('g')
      .attr('transform', (d: any) => { return `translate(${d.x}, ${d.y})`; })
      .on('click', () => this.nodeClick())
      .on('mouseenter', () => this.nodeMouseEnter())
      .on('mouseleave', () => this.nodeMouseLeave())
      .call(d3.drag()
        .on('start', () => this.dragStart())
        .on('drag', () => this.drag())
        .on('end', () => this.dragEnd())
      );

    newNodes.append('circle')
      .attr('r', '60')
      .classed('error', (d: ProcessWrapper) => {
        return d.errors;
      })
      .classed('node', true);

    newNodes.append('text')
      .attr('text-anchor', 'middle')
      .text((d: any) => { return d.display(); });
  }
}
