import bar_chart_race as bcr

class VideoGenerator:
    @staticmethod
    def generate_video(df, output_path, title):
        bcr.bar_chart_race(
            df=df,
            filename=output_path,
            title=title,
            steps_per_period=10,
            period_length=500,
            figsize=(12, 8)
        )