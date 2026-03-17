import streamlit as st
import pandas as pd
import plotly.express as px
from googleapiclient.discovery import build

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(
    page_title="YouTube Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

# ----------------------------
# DARK THEME STYLE
# ----------------------------
st.markdown("""
<style>
body {
    background-color: #0e1117;
}
.metric-card {
    background-color:#1c1f26;
    padding:15px;
    border-radius:10px;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 YouTube Analytics Dashboard")
st.write("Analyze YouTube channel performance and engagement.")

# ----------------------------
# SIDEBAR
# ----------------------------
st.sidebar.header("Dashboard Controls")
channel_name = st.sidebar.text_input("Enter Channel Name")

# ----------------------------
# API SETUP
# ----------------------------
API_KEY = "Enter your api_key"

youtube = build("youtube", "v3", developerKey=API_KEY)

# ----------------------------
# GET CHANNEL ID
# ----------------------------
def get_channel_id(channel_name):

    request = youtube.search().list(
        part="snippet",
        q=channel_name,
        type="channel",
        maxResults=1
    )

    response = request.execute()

    return response["items"][0]["snippet"]["channelId"]


# ----------------------------
# CHANNEL INFO
# ----------------------------
def get_channel_info(channel_id):

    request = youtube.channels().list(
        part="snippet,statistics",
        id=channel_id
    )

    response = request.execute()

    item = response["items"][0]

    return {
        "title": item["snippet"]["title"],
        "logo": item["snippet"]["thumbnails"]["high"]["url"],
        "subs": int(item["statistics"]["subscriberCount"]),
        "views": int(item["statistics"]["viewCount"]),
        "videos": int(item["statistics"]["videoCount"])
    }


# ----------------------------
# GET VIDEOS
# ----------------------------
def get_videos(channel_id):

    request = youtube.search().list(
        part="snippet",
        channelId=channel_id,
        maxResults=20,
        order="date"
    )

    response = request.execute()

    videos = []

    for item in response["items"]:

        if item["id"]["kind"] == "youtube#video":

            videos.append({
                "VideoID": item["id"]["videoId"],
                "Title": item["snippet"]["title"],
                "Thumbnail": item["snippet"]["thumbnails"]["high"]["url"]
            })

    return videos


# ----------------------------
# VIDEO STATS
# ----------------------------
def get_video_stats(video_data):

    ids = [v["VideoID"] for v in video_data]

    request = youtube.videos().list(
        part="statistics",
        id=",".join(ids)
    )

    response = request.execute()

    stats = []

    for i, video in enumerate(response["items"]):

        stat = video["statistics"]

        stats.append({
            "Title": video_data[i]["Title"],
            "Thumbnail": video_data[i]["Thumbnail"],
            "Views": int(stat.get("viewCount",0)),
            "Likes": int(stat.get("likeCount",0)),
            "Comments": int(stat.get("commentCount",0))
        })

    df = pd.DataFrame(stats)

    df["Engagement Rate"] = (df["Likes"] + df["Comments"]) / df["Views"]

    return df


# ----------------------------
# DASHBOARD
# ----------------------------
if channel_name:

    channel_id = get_channel_id(channel_name)

    channel = get_channel_info(channel_id)

    # Channel header
    col1, col2 = st.columns([1,4])

    with col1:
        st.image(channel["logo"])

    with col2:
        st.header(channel["title"])

    st.divider()

    # KPI metrics
    m1, m2, m3 = st.columns(3)

    m1.metric("Subscribers", f"{channel['subs']:,}")
    m2.metric("Total Views", f"{channel['views']:,}")
    m3.metric("Total Videos", f"{channel['videos']:,}")

    st.divider()

    videos = get_videos(channel_id)

    df = get_video_stats(videos)

    # ----------------------------
    # TOP VIDEOS CHART
    # ----------------------------
    st.subheader("Top Performing Videos")

    top_videos = df.sort_values("Views", ascending=False).head(10)

    fig_top = px.bar(
        top_videos,
        x="Title",
        y="Views",
        color="Views",
        title="Top 10 Videos by Views",
        animation_frame=None
    )

    st.plotly_chart(fig_top, use_container_width=True)

    # ----------------------------
    # LIKES TREND
    # ----------------------------
    st.subheader("Likes Trend")

    fig_likes = px.line(
        df,
        y="Likes",
        markers=True,
        title="Likes Trend"
    )

    st.plotly_chart(fig_likes, use_container_width=True)

    # ----------------------------
    # ENGAGEMENT SCATTER
    # ----------------------------
    st.subheader("Engagement Analysis")

    fig_eng = px.scatter(
        df,
        x="Views",
        y="Engagement Rate",
        size="Likes",
        hover_name="Title",
        title="Engagement vs Views"
    )

    st.plotly_chart(fig_eng, use_container_width=True)

    st.divider()

    # ----------------------------
    # VIDEO CARDS
    # ----------------------------
    st.subheader("Recent Videos")

    cols = st.columns(4)

    for i, video in enumerate(df.head(8).to_dict("records")):

        with cols[i % 4]:
            st.image(video["Thumbnail"])
            st.caption(video["Title"])
            st.write(f"Views: {video['Views']:,}")

    st.divider()

    # ----------------------------
    # DATA TABLE
    # ----------------------------
    st.subheader("Video Analytics Data")

    st.dataframe(df, use_container_width=True)


# ----------------------------
# FOOTER
# ----------------------------
st.markdown("---")
st.markdown("Dashboard built with **Streamlit + YouTube Data API**")