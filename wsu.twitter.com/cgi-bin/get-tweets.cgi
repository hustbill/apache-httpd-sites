#!/usr/bin/perl -wT

#
# HTTP GET
# get-tweets.cgi
# get-tweets.cgi?date=2013-03-14%2014:15:01
#
# If no query string provided we get *all* tweets.
# Otherwise we only fetch tweets with time stamps
# later than the given date.
#
# Returns JSON object (on success):
#  {"tweets" = [ 
#     { "tweet_id" : 1234,
#       "username" : "wcochran",
#       "time_stamp" : "2013-03-14 14:15:01",
#       "isdeleted" 0,
#       "tweet" : "Yo yo yo"}, ... ] }
#

use strict;
use CGI;
use DBI;
#use HTML::Entities;
use JSON;

my $cgi = new CGI;

my $DB = "wsu-twitter.db";
my $TWEETS = "tweets";
my $USERS = "users";

my $dbh = DBI->connect("DBI:SQLite:dbname=$DB", "", "");
unless ($dbh) {
    print $cgi->header(-type => "application/json", 
		       -charset => "utf-8",
		       -status => "503 Database Unavailable");
    exit 1;
}

my $refresh_date = $cgi->param("date");

my $query = 
    "SELECT tweet_id, username, time_stamp, tweet, isdeleted ".
    "FROM $TWEETS, $USERS WHERE $TWEETS.user_id = $USERS.user_id";
$query .= " AND time_stamp > '$refresh_date'" if length($refresh_date) > 0;

my $sth = $dbh->prepare($query);
unless (defined $sth->execute()) {
    print $cgi->header(-type => "application/json", 
		       -charset => "utf-8",
		       -status => "500 Internal Server Error");
    exit 1;
}

my $rows = $sth->fetchall_arrayref();
$sth->finish();
print $cgi->header(-type => "application/json", 
		   -charset => "utf-8");

#
# We buffer all tweets -- may be better to output one
# tweet at a time.
#

my @tweets;

foreach my $row (@$rows) {
    my ($tweet_id, $username, $time_stamp, $tweet, $isdeleted) = @$row;
    my $obj = {"tweet_id" => $tweet_id,
	       "username" => $username,
	       "time_stamp" => $time_stamp,
	       "tweet" => $tweet,
	       "isdeleted" => $isdeleted};
    push @tweets, $obj;
}

print encode_json({"tweets" => \@tweets});

$dbh->disconnect;
