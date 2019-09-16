# -*- coding: utf-8 -*-
"""
Created on Fri Feb 15 22:20:09 2019

@author: Rdebbout
"""
import geopandas as gpd

import requests
#import numpy as np
import pandas as pd
#import pymysql.cursors
from bs4 import BeautifulSoup
#from selenium import webdriver
#from datetime import datetime



headers = {'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/69.0.3497.100 Safari/537.36')}

url = 'https://en.wikipedia.org/wiki/List_of_U.S._states_by_homicide_rate'
response  = requests.get(url, headers=headers)
data = response.text
soup = BeautifulSoup(data, features="html.parser")
tbl = soup.find('table')
rows = tbl.findAll('tr')
columns = [e.text.replace('\n','') for e in rows[0].findAll('th')]
final = pd.DataFrame(columns=columns)

for idx, row in enumerate(rows[1:]):
    final.loc[idx] = [e.text.replace('\n','').replace('\xa0','') for e in row.findAll('td')]


###############################################################################
import json

from shapely import affinity
from shapely.geometry import mapping, shape


def get_geojson():
    with open('us_states_simplified_albers.geojson') as us_states_file:
        geojson = json.loads(us_states_file.read())
        for f in geojson['features']:
            if f['properties']['NAME'] == 'Alaska':
                geom = affinity.translate(shape(f['geometry']), xoff=1.2e6, yoff=-4.8e6)
                geom = affinity.scale(geom, .4, .4)
                geom = affinity.rotate(geom, 30)
                f['geometry'] = mapping(geom)
            elif f['properties']['NAME'] == 'Hawaii':
                geom = affinity.translate(shape(f['geometry']), xoff=4.6e6, yoff=-1.1e6)
                geom = affinity.rotate(geom, 30)
                f['geometry'] = mapping(geom)
    return json.dumps(geojson)    

geojson = get_geojson()
[x for x in geojson]

from bokeh.models import HoverTool
from bokeh.plotting import figure, show, output_file, ColumnDataSource
from bokeh.sampledata.us_states import data as states
from bokeh.models import LogColorMapper
from bokeh.palettes import Viridis6 as palette
from bokeh.models import GeoJSONDataSource
states.pop('DC')
state_xs = [state["lons"] for state in states.values()]
state_ys = [state["lats"] for state in states.values()]

colors = ["#F1EEF6", "#D4B9DA", "#C994C7", "#DF65B0", "#DD1C77", "#980043"]
sorter = pd.DataFrame(columns=['wookie'])
for idx, name in enumerate(states):
    sorter.loc[idx] = [states[name]['name']]        
       
final = pd.merge(sorter, final, left_on='wookie', right_on='State').drop('wookie',axis=1)



assert [states[name]['name'] for name in states] == final.State.tolist()
          
###############################################################################          
from bokeh.sampledata.sample_geojson import geojson
state_names = final.State.tolist()
state_rates_2017 = final['2017'].tolist()
state_rates_2014 = final['2014'].tolist()
state_rates_2010 = final['2010'].tolist()
state_rates_2005 = final['2005'].tolist()
state_rates_2000 = final['2000'].tolist()
state_rates_1996 = final['1996'].tolist()
county_colors = [colors[int(rate/3)] for rate in county_rates]

#source = ColumnDataSource(data=dict(
#    x=state_xs,
#    y=state_ys,
#    color=colors,
#    name=state_names,
#    rate=state_rates_2017,
#))
color_mapper = LogColorMapper(palette=palette)
data=dict(
    x=state_xs,
    y=state_ys,
    name=state_names,
    rate=state_rates_2017,
)

TOOLS="pan,wheel_zoom,box_zoom,reset,hover,save"

#p = figure(title="Texas Unemployment 2009", tools=TOOLS)

p = figure(
    title="Texas Unemployment, 2009", tools=TOOLS,
    x_axis_location=None, y_axis_location=None,
    tooltips=[
        ("Name", "@name"), ("Unemployment rate)", "@rate%"), ("(Long, Lat)", "($x, $y)")
    ])
p.grid.grid_line_color = None
p.hover.point_policy = "follow_mouse"
#p.patches('x', 'y', source=source,
#          fill_color='color', fill_alpha=0.7,
#          line_color="white", line_width=0.5)
geo_source = GeoJSONDataSource(geojson=geojson)
p = figure(background_fill_color="lightgrey")
p.patches('x', 'y', source=geo_source,
#          fill_color=["firebrick"]*50,
          fill_alpha=0.7, line_color="black", line_width=0.5)

p.patches('x', 'y', source=data,
          fill_color={'field': 'rate', 'transform': color_mapper},
          fill_alpha=0.7, line_color="white", line_width=0.5)



hover = p.select_one(HoverTool)
hover.point_policy = "follow_mouse"
hover.tooltips = [
    ("Name", "@name"),
    ("Unemployment rate)", "@rate%"),
    ("(Long, Lat)", "($x, $y)"),
]

output_file("texas.html", title="texas.py example")

show(p)          





# working from here...down


fig = figure(plot_width=1250, plot_height=600, x_range=(-3e6, 3e6), y_range=(-2e6, 1.5e6))
fig.grid.grid_line_alpha = 0
fig.axis.visible = False
fig.patches(xs='xs', ys='ys', 
            line_color='white', 
            color=dict(transform=color_mapper,field='CENSUSAREA'),
            source=GeoJSONDataSource(geojson=get_geojson()), 
            alpha=.85)


hover = HoverTool()

hover.tooltips = """    
        <div>
            <span style="font-size: 17px; font-weight: bold;">@NAME</span>
        </div>
        <div>
            <span style="font-size: 15px; color: orange;">@CENSUSAREA</span>
            <span style="font-size: 15px;">deer-involved accidents</span>
        </div>

    """
hover.point_policy = "follow_mouse"
fig.add_tools(hover)   
    
output_file('translate_map.html')
show(fig)
#######################################################################
#responsive

import pandas as pd
import numpy as np

from bokeh.io import show, output_notebook, push_notebook
from bokeh.plotting import figure

from bokeh.models import CategoricalColorMapper, HoverTool, ColumnDataSource, Panel
from bokeh.models.widgets import CheckboxGroup, Slider, RangeSlider, Tabs

from bokeh.layouts import column, row, WidgetBox
from bokeh.palettes import Category20_16

from bokeh.application.handlers import FunctionHandler
from bokeh.application import Application


flights = pd.read_csv('complete_flights.csv', index_col=0)[['arr_delay', 'carrier', 'name']]
flights.head()

available_carriers = list(flights['name'].unique())
available_carriers.sort()

def modify_doc(doc):
    
    def make_dataset(carrier_list, range_start = -60, range_end = 120, bin_width = 5):

        by_carrier = pd.DataFrame(columns=['proportion', 'left', 'right', 
                                           'f_proportion', 'f_interval',
                                           'name', 'color'])
        range_extent = range_end - range_start

        # Iterate through all the carriers
        for i, carrier_name in enumerate(carrier_list):

            # Subset to the carrier
            subset = flights[flights['name'] == carrier_name]

            # Create a histogram with 5 minute bins
            arr_hist, edges = np.histogram(subset['arr_delay'], 
                                           bins = int(range_extent / bin_width), 
                                           range = [range_start, range_end])

            # Divide the counts by the total to get a proportion
            arr_df = pd.DataFrame({'proportion': arr_hist / np.sum(arr_hist), 'left': edges[:-1], 'right': edges[1:] })

            # Format the proportion 
            arr_df['f_proportion'] = ['%0.5f' % proportion for proportion in arr_df['proportion']]

            # Format the interval
            arr_df['f_interval'] = ['%d to %d minutes' % (left, right) for left, right in zip(arr_df['left'], arr_df['right'])]

            # Assign the carrier for labels
            arr_df['name'] = carrier_name

            # Color each carrier differently
            arr_df['color'] = Category20_16[i]

            # Add to the overall dataframe
            by_carrier = by_carrier.append(arr_df)

        # Overall dataframe
        by_carrier = by_carrier.sort_values(['name', 'left'])

        return ColumnDataSource(by_carrier)
    
    def style(p):
        # Title 
        p.title.align = 'center'
        p.title.text_font_size = '20pt'
        p.title.text_font = 'serif'

        # Axis titles
        p.xaxis.axis_label_text_font_size = '14pt'
        p.xaxis.axis_label_text_font_style = 'bold'
        p.yaxis.axis_label_text_font_size = '14pt'
        p.yaxis.axis_label_text_font_style = 'bold'

        # Tick labels
        p.xaxis.major_label_text_font_size = '12pt'
        p.yaxis.major_label_text_font_size = '12pt'

        return p
    
    def make_plot(src):
        # Blank plot with correct labels
        p = figure(plot_width = 700, plot_height = 700, 
                  title = 'Histogram of Arrival Delays by Carrier',
                  x_axis_label = 'Delay (min)', y_axis_label = 'Proportion')

        # Quad glyphs to create a histogram
        p.quad(source = src, bottom = 0, top = 'proportion', left = 'left', right = 'right',
               color = 'color', fill_alpha = 0.7, hover_fill_color = 'color', legend = 'name',
               hover_fill_alpha = 1.0, line_color = 'black')

        # Hover tool with vline mode
        hover = HoverTool(tooltips=[('Carrier', '@name'), 
                                    ('Delay', '@f_interval'),
                                    ('Proportion', '@f_proportion')],
                          mode='vline')

        p.add_tools(hover)

        # Styling
        p = style(p)

        return p
    
    def update(attr, old, new):
        carriers_to_plot = [carrier_selection.labels[i] for i in carrier_selection.active]
        
        new_src = make_dataset(carriers_to_plot,
                               range_start = range_select.value[0],
                               range_end = range_select.value[1],
                               bin_width = binwidth_select.value)

        src.data.update(new_src.data)

        
    carrier_selection = CheckboxGroup(labels=available_carriers, active = [0, 1])
    carrier_selection.on_change('active', update)
    
    binwidth_select = Slider(start = 1, end = 30, 
                         step = 1, value = 5,
                         title = 'Delay Width (min)')
    binwidth_select.on_change('value', update)
    
    range_select = RangeSlider(start = -60, end = 180, value = (-60, 120),
                               step = 5, title = 'Delay Range (min)')
    range_select.on_change('value', update)
    
    
    
    initial_carriers = [carrier_selection.labels[i] for i in carrier_selection.active]
    
    src = make_dataset(initial_carriers,
                      range_start = range_select.value[0],
                      range_end = range_select.value[1],
                      bin_width = binwidth_select.value)
    
    p = make_plot(src)
    
    # Put controls in a single element
    controls = WidgetBox(carrier_selection, binwidth_select, range_select)
    
    # Create a row layout
    layout = row(controls, p)
    
    # Make a tab with the layout 
    tab = Panel(child=layout, title = 'Delay Histogram')
    tabs = Tabs(tabs=[tab])
    
    doc.add_root(tabs)
    
# Set up an application
handler = FunctionHandler(modify_doc)
app = Application(handler)
show(app)

polys = gpd.read_file('us_states_simplified_albers.geojson')
polys.columns.tolist()
[n for n in polys.NAME if not n in final.State.tolist()]
merged = polys.merge(final, left_on='NAME', right_on='State', how='inner')
type(merged)

with open('us_states_simplified_albers.geojson') as us_states_file:
    geojson = json.loads(us_states_file.read())

years = ["2017", "2014", "2010", "2005", "2000", "1996"]
remove = []
for f in geojson['features']:
    print(f['properties']['NAME'])
    if f['properties']['NAME'] not in final.index.tolist():
#        print(f['properties']['NAME'])
        remove.append(geojson['features'].index(f))
    else:
        row = final.loc[f['properties']['NAME']]
        print(row)
        for year in years:
            f['properties'][year] = row[year]
for x in remove:
    del geojson['features'][x] 

for f in geojson['features']:
    print(f['properties']['NAME'])
    
    if f['properties']['NAME'] == 'Florida':
        break
def match_states(states_json):
    return states_json['properties']['NAME'] in final.index.tolist()

geojson['features'] = list(filter(match_states,geojson['features']))

Florida

        
final.set_index('State',inplace=True)        
        
type(geojson['features'])
geojson['features'].index(f)
del geojson['features'][geojson['features'].index(f)]
