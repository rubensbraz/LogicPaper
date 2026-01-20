# 🧪 Generate Mock Data

To test the system without manual file creation, use the `generate_seeds.py` script. It automatically creates:

* A structured **Excel** file with edge cases.
* **Word** and **PowerPoint** templates with Jinja2 tags.
* An **Assets ZIP** file with dummy images.

## How to Run

Run the following command in your terminal:

```bash
docker exec -it logicpaper_core python /data/mock_data/generate_seeds.py
```
