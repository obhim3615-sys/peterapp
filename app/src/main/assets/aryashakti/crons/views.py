from django.shortcuts import render
from django.db.models import F, Q
from datetime import date,datetime,timedelta
import requests, math, time, multiprocessing
from django.core.paginator import Paginator, EmptyPage

from app_farm.models import farm
from app_farm.utils.helper import calculate_magnitude
from farm_category.models import FarmsCategory,Category
from subscription_service.models import UserService

# Create your views here.

def DeductValidityDays():
    today_date = date.today()
    # Assuming 'days' is the value for unit that represents the time-based validity
    user_services_to_decrement = UserService.objects.filter(user_subscription__validity__gt=today_date,service__unit='days', remaining__gt=0)

    # Decrement the remaining field by 1 for entries with unit 'days' and remaining > 0
    user_services_to_decrement.update(remaining=F('remaining') - 1)

def run_categorization_logic(plot_id, season_id, categories, farm_id):
    stress_map = {
        'biotic': 'I003',
        # 'whole': 'I011'
    }
    result = {
        'success': True,
        'date': datetime.now()
    }
    plot_ids = plot_id.split('_')
    for stress in stress_map:
        for i in range(0,7):
            date_str = (result['date'] - timedelta(days=i)).strftime("%Y-%m-%d")
            # Fetch the GEO JSON data
            if stress == 'biotic':
                url = 'https://datasciencesdiag.blob.core.windows.net/myplots/arya-ag/aryafpo/geojson/'+plot_ids[0]+'/'+plot_id+'_aryafpo_'+date_str+'_biotic_stress.geojson'
            else:
                url = 'https://datasciencesdiag.blob.core.windows.net/myplots/myplots-lt/newindices/astress/sendingI011d/'+plot_ids[0]+'_'+(plot_ids[2] if len(plot_ids) == 3 else plot_ids[1])+'_'+date_str+'_merged.geojson'
            
            # Fetch the GEO JSON data
            # points = requests.get(url)
            while True:
                count = 0
                try:
                    points = requests.get(url)
                    break
                except requests.exceptions.ConnectionError:
                    count = count + 1
                    # print(str(farm_id) + " =--> ", "Connection error")
                    if count == 3:
                        break
                    else:
                        time.sleep(0.2)


            if points.status_code == 204 or points.status_code == 404:
                # print("1234",time.time()*1000)
                # # Fetch the URL for GEO JSON api
                # url = "https://plots.prakshep.com/myplots/geojsonview?prakshep_id=" + plot_id + '&season_id='+ season_id + '&secret_key=' + settings.PRAKSHEP_KEY + '&index_id=' + stress_map[stress] + '&date_of_analysis=' + result['date']
                # geo_json_url = requests.get(url)
                # if geo_json_url.status_code == 404 or geo_json_url.status_code == 204:
                #     print(str(farm_id) + " =--> ", "Can't fetch the URL for - " + stress_map[stress],time.time()*1000)
                #     continue
                # geo_json_url = geo_json_url.json()

                # # Fetch the GEO JSON data
                # points = requests.get(geo_json_url['data'][0]['index_geojson_url'])
                # if points.status_code == 204:
                print(str(farm_id) + ' (' + date_str + ') ' + " =--> ", "Can't fetch the Coordinates for - " + stress_map[stress])
            else:
                break

        if points.status_code != 200:
            continue

        points = points.json()

        if stress != 'whole':
            # Calculate the total green, red, yellow points
            total_points = {
                'green': 0,
                'yellow': 0,
                'red': 0
            }
            # print(points)
            # for p in points['features'].copy():
            for p in points['features']:
                if p['properties']['fill'] == '#52ce60':
                    for coordinates in p['geometry']['coordinates']:
                        if p['geometry']['type'] == 'MultiPolygon':
                            for temp_coordinates in coordinates:
                                total_points['green'] += len(temp_coordinates)
                        else:
                            total_points['green'] += len(coordinates)

                    # Remove the green points
                    # points['features'].remove(p)
                elif p['properties']['fill'] == '#e30808':
                    for coordinates in p['geometry']['coordinates']:
                        if p['geometry']['type'] == 'MultiPolygon':
                            for temp_coordinates in coordinates:
                                total_points['red'] += len(temp_coordinates)
                        else:
                            total_points['red'] += len(coordinates)
                elif p['properties']['fill'] == '#cec652':
                    for coordinates in p['geometry']['coordinates']:
                        if p['geometry']['type'] == 'MultiPolygon':
                            for temp_coordinates in coordinates:
                                total_points['yellow'] += len(temp_coordinates)
                        else:
                            total_points['yellow'] += len(coordinates)

            # Ratio of points to 100
            temp_point = []
            for color in total_points:
                temp_point.append(round((total_points[color] / (total_points['green']+total_points['red']+total_points['yellow'])) * 100))

            # Calculate the distance and find min distance from all categories.
            min_distance = math.inf
            index = None
            for i, category in enumerate(categories):
                point = [category.healthy,category.stress,category.damaged]
                distance = math.dist(temp_point, point)
                if distance < min_distance:
                    min_distance = distance
                    index = i

            result[stress+'_category'] = categories[index]
        result[stress+'_points'] = points['features']

    return result

def update_farm_maps(index):
    # print(index," STARTING!!! -- ", str(int(time.time()*1000)), datetime.now().strftime("%Y-%m-%d"))
    categories = Category.objects.all()
    farms = farm.objects.exclude(Q(my_plot_id__isnull=True)|Q(season_id__isnull=True) | Q(latitude__isnull=True)|Q(longitude__isnull=True)).exclude(Q(my_plot_id__exact='') | Q(season_id__exact='')).order_by('id')[((index-1)*1000): (index*1000)]
    # print('total farms = '+str(len(farms)))

    for f in farms:
        try:
            result = run_categorization_logic(f.my_plot_id, f.season_id, categories, f.id)

            if result['success']:
                if result.get('biotic_points') or result.get('whole_points'):
                    obj = {}
                    if result.get('biotic_points'):
                        obj['biotic_map'] = result.get('biotic_points')
                        obj['biotic_category'] = result.get('biotic_category')
                    if result.get('whole_points'):
                        obj['whole_map'] = result.get('whole_points')

                    FarmsCategory.objects.update_or_create(
                        farm = f,
                        defaults={**obj}
                    )
                    # print(str(f.id) + " --> ", 'SUCCESS')
            else:
                print(str(f.id) + " ---> ", result['err'])
        except Exception as e:
            print(str(f.id) + " ----> ", e)
    # print("ENDED!!! -- ", str(int(time.time()*1000)))

# Define the function that processes a chunk of data
def process_chunk(farms, categories):
    # Your processing logic for the chunk goes here
    print("STARTING!!! -- ", str(int(time.time()*1000)), datetime.now().strftime("%Y-%m-%d"))
    for f in farms:
        try:
            result = run_categorization_logic(f.my_plot_id, f.season_id, categories, f.id)

            if result['success']:
                if result.get('biotic_points') or result.get('whole_points'):
                    obj = {}
                    if result.get('biotic_points'):
                        obj['biotic_map'] = result.get('biotic_points')
                        obj['biotic_category'] = result.get('biotic_category')
                    if result.get('whole_points'):
                        obj['whole_map'] = result.get('whole_points')

                    FarmsCategory.objects.update_or_create(
                        farm = f,
                        defaults={**obj}
                    )
                    print(str(f.id) + " --> ", 'SUCCESS')
            else:
                print(str(f.id) + " ---> ", result['err'])
        except Exception as e:
            print(str(f.id) + " ----> ", e)
    print("ENDED!!! -- ", str(int(time.time()*1000)))

def run_parallel_jobs(paginator, num_processes, categories):
    print('sssss -----  ', str(int(time.time()*1000)))
    with multiprocessing.Pool(processes=num_processes) as pool:
        # Use the Paginator to get a page of data for each process
        print(paginator.num_pages)
        for page_num in range(1, paginator.num_pages + 1):
            try:
                data_chunk = paginator.page(page_num)
                #print(len(data_chunk),page_num)
                pool.apply_async(process_chunk, args=(data_chunk, categories))
            except EmptyPage:
                # Handle the case where there are no more pages
                break
        pool.close()
        pool.join()
        print('eeeeee -----  ',str(int(time.time()*1000)))

# In your Django cron job
def my_cron_job():
    try:
        # Fetch data from the database or any other source as a QuerySet
        categories = Category.objects.all()
        farms = farm.objects.exclude(Q(my_plot_id__isnull=True)|Q(season_id__isnull=True) | Q(latitude__isnull=True)|Q(longitude__isnull=True)).exclude(Q(my_plot_id__exact='') | Q(season_id__exact='')).exclude(id=898).filter(is_manual_updated=False).order_by('id')
        # print('total farms = '+str(len(farms)))

        # Calculate the magnitude of each category and also sort the categories according to magnitude value.
        for category in categories:
            category.magnitude = calculate_magnitude([category.healthy,category.stress,category.damaged])

        sorted_categories = sorted(categories, key=lambda category: category.magnitude)

        # Define the number of processes
        num_processes = multiprocessing.cpu_count()
        # print(num_processes)

        # Create a Paginator to split the QuerySet into chunks
        paginator = Paginator(farms, num_processes)

        # Run the chunks in parallel
        run_parallel_jobs(paginator, num_processes, sorted_categories)
    except Exception as e:
        print(" --> ", e)
